from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

# Add logger
_logger = logging.getLogger(__name__)

class MrpRequisition(models.Model):
    _name = 'dw.mrp.requisition'
    _description = 'Manufacturing Requisition Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    
    name = fields.Char(
        string='Requisition Number',
        required=True,
        readonly=True,
        default=lambda self: _('New')
    )
    date = fields.Date(
        string='Requisition Date',
        default=fields.Date.today
    )
    department = fields.Selection([
        ('manufacturing', 'Manufacturing'),
        ('production', 'Production'),
        ('assembly', 'Assembly'),
        ('finishing', 'Finishing'),
        ('store', 'Store')
    ], string='Department', required=True, default='store')
    
    requested_by = fields.Many2one(
        'res.users',
        string='Requested By',
        default=lambda self: self.env.user
    )
    required_date = fields.Date(
        string='Required Date',
        required=True
    )
    
    manufacturing_order_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Order',
        domain="[('state', 'in', ['confirmed', 'progress'])]"
    )
    
    requisition_line_ids = fields.One2many(
        'dw.mrp.requisition.line',
        'requisition_id',
        string='Items'
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted to Store'),
        ('ready_for_transfer', 'Ready for Internal Transfer'),
        ('requested_other_location', 'Requested to Another Location'),
        ('completed', 'Completed')
    ], string='Status', default='draft')
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    notes = fields.Text(string='Internal Notes')
    
    source_location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        domain="[('usage', '=', 'internal')]",
        required=True,
        default=lambda self: self._get_default_source_location()
    )
    destination_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location', 
        domain="[('usage', '=', 'internal')]",
        required=True,
        default=lambda self: self._get_default_destination_location()
    )
    
    internal_transfer_id = fields.Many2one(
        'stock.picking',
        string='Internal Transfer',
        readonly=True
    )
    requested_location_id = fields.Many2one(
        'stock.location',
        string='Requested Location',
        domain="[('usage', '=', 'internal')]"
    )
    
    total_items = fields.Integer(
        string='Total Items',
        compute='_compute_total_items'
    )
    total_quantity = fields.Float(
        string='Total Quantity',
        compute='_compute_total_quantity'
    )
    
    @api.depends('requisition_line_ids')
    def _compute_total_items(self):
        for requisition in self:
            requisition.total_items = len(requisition.requisition_line_ids)
    
    @api.depends('requisition_line_ids.quantity')
    def _compute_total_quantity(self):
        for requisition in self:
            requisition.total_quantity = sum(line.quantity for line in requisition.requisition_line_ids)
    
    def _get_default_source_location(self):
        """Get default source location from stock settings"""
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        return picking_type.default_location_src_id if picking_type else False
    
    def _get_default_destination_location(self):
        """Get default destination location from stock settings"""
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        return picking_type.default_location_dest_id if picking_type else False
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('dw.mrp.requisition') or _('New')
        return super().create(vals)
    
    def _check_manufacturing_user_permission(self):
        """Check if current user is a manufacturing user and owns the requisition"""
        is_manufacturing_user = self.env.user.has_group('dw_stock_requisition.group_manufacturing_team')
        is_admin = self.env.user.has_group('base.group_erp_manager')  # Built-in admin group
        is_requester = self.requested_by == self.env.user
        return (is_manufacturing_user and is_requester) or is_admin
    
    def _check_inventory_user_permission(self):
        """Check if current user is an inventory user or admin"""
        is_inventory_user = self.env.user.has_group('dw_stock_requisition.group_inventory_team')
        is_admin = self.env.user.has_group('base.group_erp_manager')  # Built-in admin group
        return is_inventory_user or is_admin
    
    def action_submit_to_store(self):
        """Submit requisition to store - Only manufacturing users can submit their own drafts"""
        for requisition in self:
            if requisition.state != 'draft':
                raise UserError(_("Only draft requisition can be submitted."))
            
            if not requisition._check_manufacturing_user_permission():
                raise UserError(_("You can only submit your own draft requisition."))
            
            # Admin can submit any requisition, manufacturing users only their own
            if not self.env.user.has_group('base.group_erp_manager') and requisition.requested_by != self.env.user:
                raise UserError(_("You can only submit your own requisition."))
            
            if not requisition.requisition_line_ids:
                raise UserError(_("Cannot submit requisition without any items."))
            
            if not requisition.source_location_id or not requisition.destination_location_id:
                raise UserError(_("Please set both source and destination locations."))
            
            requisition.state = 'submitted'
        return True
    
    def action_ready_for_internal_transfer(self):
        """Create Internal Transfer - Only inventory users can process submitted requisition"""
        for requisition in self:
            if requisition.state != 'submitted':
                raise UserError(_("Only submitted requisition can be processed for transfer."))
            
            if not requisition._check_inventory_user_permission():
                raise UserError(_("Only inventory users can process requisition."))
            
            if not requisition.requisition_line_ids:
                raise UserError(_("Cannot create transfer without any items."))
            
            if not requisition.source_location_id:
                raise UserError(_("Please set source location."))
            if not requisition.destination_location_id:
                raise UserError(_("Please set destination location."))
            
            # Check if all products are available in source location
            for line in requisition.requisition_line_ids:
                available_qty = line.product_id.with_context(
                    location=requisition.source_location_id.id
                ).qty_available
                
                if available_qty < line.quantity:
                    raise UserError(_(
                        "Product %s is not available in sufficient quantity at %s. Available: %s, Required: %s"
                    ) % (line.product_id.name, requisition.source_location_id.name, available_qty, line.quantity))
            
            # IMPROVED: Robust picking type search with multiple fallbacks
            picking_type = self._find_or_create_internal_picking_type(requisition.company_id)
            
            if not picking_type:
                raise UserError(_(
                    "No internal transfer operation type found. Please contact your administrator to set up Inventory operations."
                ))
            
            # Create picking with proper values
            picking_vals = {
                'picking_type_id': picking_type.id,
                'location_id': requisition.source_location_id.id,
                'location_dest_id': requisition.destination_location_id.id,
                'origin': f"Requisition: {requisition.name}",
                'scheduled_date': requisition.required_date,
                'company_id': requisition.company_id.id,
                'move_type': 'direct',
                'priority': '1',
            }
            
            picking = self.env['stock.picking'].create(picking_vals)
            
            # Create move lines
            for line in requisition.requisition_line_ids:
                move_vals = {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom': line.uom_id.id,
                    'product_uom_qty': line.quantity,
                    'picking_id': picking.id,
                    'location_id': requisition.source_location_id.id,
                    'location_dest_id': requisition.destination_location_id.id,
                    'company_id': requisition.company_id.id,
                }
                self.env['stock.move'].create(move_vals)
            
            requisition.internal_transfer_id = picking.id
            requisition.state = 'ready_for_transfer'
            
            # Confirm and assign the transfer
            picking.action_confirm()
            picking.action_assign()
            
            # Show success message
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Transfer Created'),
                    'message': _('Internal transfer %s has been created successfully.') % picking.name,
                    'sticky': False,
                }
            }
        return True

    def _find_or_create_internal_picking_type(self, company):
        """Find or create an internal picking type with multiple fallbacks"""
        # Try multiple search strategies
        search_domains = [
            [('code', '=', 'internal'), ('company_id', '=', company.id)],
            [('code', '=', 'internal'), ('company_id', '=', False)],
            [('code', '=', 'internal')],
            [('name', 'ilike', 'internal'), ('company_id', '=', company.id)],
            [('name', 'ilike', 'internal')],
        ]
        
        for domain in search_domains:
            picking_type = self.env['stock.picking.type'].search(domain, limit=1)
            if picking_type:
                return picking_type
        
        # If no picking type found, try to create one
        return self._create_default_internal_picking_type(company)

    def _create_default_internal_picking_type(self, company):
        """Create a default internal picking type"""
        try:
            # Get default locations
            stock_location = self.env.ref('stock.stock_location_stock')
            if not stock_location:
                # If stock location doesn't exist, search for any internal location
                stock_location = self.env['stock.location'].search([
                    ('usage', '=', 'internal')
                ], limit=1)
            
            if not stock_location:
                raise UserError(_("No internal stock locations found. Please set up inventory locations first."))
            
            # Create the picking type
            picking_type_vals = {
                'name': 'Internal Transfers',
                'code': 'internal',
                'sequence_code': 'INT',
                'default_location_src_id': stock_location.id,
                'default_location_dest_id': stock_location.id,
                'company_id': company.id,
            }
            
            return self.env['stock.picking.type'].create(picking_type_vals)
            
        except Exception as e:
            # Log the error but don't crash
            _logger.warning("Failed to create internal picking type: %s", str(e))
            return False
            
    def action_request_to_another_location(self):
        """Request products from another location - Only inventory users"""
        for requisition in self:
            if requisition.state != 'submitted':
                raise UserError(_("Only submitted requisition can be requested from other locations."))
            
            if not requisition._check_inventory_user_permission():
                raise UserError(_("Only inventory users can request from other locations."))
            
            if not requisition.requested_location_id:
                raise UserError(_("Please select a location to request from."))
            
            requisition.state = 'requested_other_location'
        return True
    
    def action_set_draft(self):
        """Reset to draft - Only original requester, inventory users, or admin can reset"""
        for requisition in self:
            is_admin = self.env.user.has_group('base.group_erp_manager')
            can_reset = (
                is_admin or
                (requisition.state == 'draft' and requisition.requested_by == self.env.user) or
                (requisition.state == 'submitted' and self.env.user.has_group('dw_stock_requisition.group_inventory_team'))
            )
            
            if not can_reset:
                raise UserError(_("You don't have permission to reset this requisition."))
            
            requisition.state = 'draft'
            requisition.message_post(
                body=_("Requisition reset to draft."),
                subject=_("Reset to Draft")
            )


# from odoo import models, fields, api, _
# from odoo.exceptions import UserError, ValidationError

# class MrpRequisition(models.Model):
#     _name = 'dw.mrp.requisition'
#     _description = 'Manufacturing Requisition Form'
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#     _order = 'date desc, id desc'
    
#     name = fields.Char(
#         string='Requisition Number',
#         required=True,
#         readonly=True,
#         default=lambda self: _('New')
#     )
#     date = fields.Date(
#         string='Requisition Date',
#         default=fields.Date.today
#     )
#     department = fields.Selection([
#         ('manufacturing', 'Manufacturing'),
#         ('production', 'Production'),
#         ('assembly', 'Assembly'),
#         ('finishing', 'Finishing'),
#         ('store', 'Store')  # Added 'store' option
#     ], string='Department', required=True, default='store')  # Default to 'store'
    
#     requested_by = fields.Many2one(
#         'res.users',
#         string='Requested By',
#         default=lambda self: self.env.user
#     )
#     required_date = fields.Date(
#         string='Required Date',
#         required=True
#     )
    
#     # Reference to Manufacturing Order
#     manufacturing_order_id = fields.Many2one(
#         'mrp.production',
#         string='Manufacturing Order',
#         domain="[('state', 'in', ['confirmed', 'progress'])]"
#     )
    
#     requisition_line_ids = fields.One2many(
#         'dw.mrp.requisition.line',
#         'requisition_id',
#         string='Items'
#     )
    
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('submitted', 'Submitted to Store'),
#         ('ready_for_transfer', 'Ready for Internal Transfer'),
#         ('requested_other_location', 'Requested to Another Location'),
#         ('completed', 'Completed')
#     ], string='Status', default='draft')
    
#     company_id = fields.Many2one(
#         'res.company',
#         string='Company',
#         default=lambda self: self.env.company
#     )
#     notes = fields.Text(string='Internal Notes')
    
#     # Location fields
#     source_location_id = fields.Many2one(
#         'stock.location',
#         string='Source Location',
#         domain="[('usage', '=', 'internal')]",
#         required=True,
#         default=lambda self: self._get_default_source_location()
#     )
#     destination_location_id = fields.Many2one(
#         'stock.location',
#         string='Destination Location', 
#         domain="[('usage', '=', 'internal')]",
#         required=True,
#         default=lambda self: self._get_default_destination_location()
#     )
    
#     # Transfer fields
#     internal_transfer_id = fields.Many2one(
#         'stock.picking',
#         string='Internal Transfer',
#         readonly=True
#     )
#     requested_location_id = fields.Many2one(
#         'stock.location',
#         string='Requested Location',
#         domain="[('usage', '=', 'internal')]"
#     )
    
#     total_items = fields.Integer(
#         string='Total Items',
#         compute='_compute_total_items'
#     )
#     total_quantity = fields.Float(
#         string='Total Quantity',
#         compute='_compute_total_quantity'
#     )
    
#     @api.depends('requisition_line_ids')
#     def _compute_total_items(self):
#         for requisition in self:
#             requisition.total_items = len(requisition.requisition_line_ids)
    
#     @api.depends('requisition_line_ids.quantity')
#     def _compute_total_quantity(self):
#         for requisition in self:
#             requisition.total_quantity = sum(line.quantity for line in requisition.requisition_line_ids)
    
#     def _get_default_source_location(self):
#         """Get default source location from stock settings"""
#         picking_type = self.env['stock.picking.type'].search([
#             ('code', '=', 'internal'),
#             ('company_id', '=', self.env.company.id)
#         ], limit=1)
#         return picking_type.default_location_src_id if picking_type else False
    
#     def _get_default_destination_location(self):
#         """Get default destination location from stock settings"""
#         picking_type = self.env['stock.picking.type'].search([
#             ('code', '=', 'internal'),
#             ('company_id', '=', self.env.company.id)
#         ], limit=1)
#         return picking_type.default_location_dest_id if picking_type else False
    
#     @api.model
#     def create(self, vals):
#         if vals.get('name', _('New')) == _('New'):
#             vals['name'] = self.env['ir.sequence'].next_by_code('dw.mrp.requisition') or _('New')
#         return super().create(vals)
    
#     # def _check_manufacturing_user_permission(self):
#     #     """Check if current user is a manufacturing user and owns the requisition"""
#     #     is_manufacturing_user = self.env.user.has_group('mrp.group_mrp_user')
#     #     is_requester = self.requested_by == self.env.user
#     #     return is_manufacturing_user and is_requester
    
#     # def _check_inventory_user_permission(self):
#     #     """Check if current user is an inventory user"""
#     #     return self.env.user.has_group('stock.group_stock_manager')
    
#     # def action_submit_to_store(self):
#     #     """Submit requisition to store - Only manufacturing users can submit their own drafts"""
#     #     for requisition in self:
#     #         if requisition.state != 'draft':
#     #             raise UserError(_("Only draft requisition can be submitted."))
            
#     #         if not requisition._check_manufacturing_user_permission():
#     #             raise UserError(_("You can only submit your own draft requisition."))
            
#     #         if not requisition.requisition_line_ids:
#     #             raise UserError(_("Cannot submit requisition without any items."))
            
#     #         if not requisition.source_location_id or not requisition.destination_location_id:
#     #             raise UserError(_("Please set both source and destination locations."))
            
#     #         requisition.state = 'submitted'
#     #         # Removed message_post to avoid email notification as per requirement
#     #     return True

#     def _check_manufacturing_user_permission(self):
#         """Check if current user is a manufacturing user and owns the requisition"""
#         is_manufacturing_user = self.env.user.has_group('dw_stock_requisition.group_manufacturing_team')
#         is_admin = self.env.user.has_group('dw_stock_requisition.group_manufacturing_requisition_admin')
#         is_requester = self.requested_by == self.env.user
#         return (is_manufacturing_user and is_requester) or is_admin
    
#     def _check_inventory_user_permission(self):
#         """Check if current user is an inventory user or admin"""
#         is_inventory_user = self.env.user.has_group('dw_stock_requisition.group_inventory_team')
#         is_admin = self.env.user.has_group('dw_stock_requisition.group_manufacturing_requisition_admin')
#         return is_inventory_user or is_admin
    
#     def action_submit_to_store(self):
#         """Submit requisition to store - Only manufacturing users can submit their own drafts"""
#         for requisition in self:
#             if requisition.state != 'draft':
#                 raise UserError(_("Only draft requisition can be submitted."))
            
#             if not requisition._check_manufacturing_user_permission():
#                 raise UserError(_("You can only submit your own draft requisition."))
            
#             # Admin can submit any requisition, manufacturing users only their own
#             if not self.env.user.has_group('dw_stock_requisition.group_manufacturing_requisition_admin') and requisition.requested_by != self.env.user:
#                 raise UserError(_("You can only submit your own requisition."))
            
#             if not requisition.requisition_line_ids:
#                 raise UserError(_("Cannot submit requisition without any items."))
            
#             if not requisition.source_location_id or not requisition.destination_location_id:
#                 raise UserError(_("Please set both source and destination locations."))
            
#             requisition.state = 'submitted'
#         return True

    
#     def action_ready_for_internal_transfer(self):
#         """Create Internal Transfer - Only inventory users can process submitted requisition"""
#         for requisition in self:
#             if requisition.state != 'submitted':
#                 raise UserError(_("Only submitted requisition can be processed for transfer."))
            
#             if not requisition._check_inventory_user_permission():
#                 raise UserError(_("Only inventory users can process requisition."))
            
#             if not requisition.requisition_line_ids:
#                 raise UserError(_("Cannot create transfer without any items."))
            
#             if not requisition.source_location_id:
#                 raise UserError(_("Please set source location."))
#             if not requisition.destination_location_id:
#                 raise UserError(_("Please set destination location."))
            
#             # Check if all products are available in source location
#             for line in requisition.requisition_line_ids:
#                 available_qty = line.product_id.with_context(
#                     location=requisition.source_location_id.id
#                 ).qty_available
                
#                 if available_qty < line.quantity:
#                     raise UserError(_(
#                         "Product %s is not available in sufficient quantity at %s. Available: %s, Required: %s"
#                     ) % (line.product_id.name, requisition.source_location_id.name, available_qty, line.quantity))
            
#             # Create Internal Transfer
#             picking_type = self.env['stock.picking.type'].search([
#                 ('code', '=', 'internal'),
#                 ('company_id', '=', requisition.company_id.id)
#             ], limit=1)
            
#             if not picking_type:
#                 raise UserError(_("No internal transfer operation type found."))
            
#             # Create picking
#             picking_vals = {
#                 'picking_type_id': picking_type.id,
#                 'location_id': requisition.source_location_id.id,
#                 'location_dest_id': requisition.destination_location_id.id,
#                 'origin': requisition.name,
#                 'scheduled_date': requisition.required_date,
#             }
            
#             picking = self.env['stock.picking'].create(picking_vals)
            
#             # Create move lines
#             for line in requisition.requisition_line_ids:
#                 move_vals = {
#                     'name': line.product_id.name,
#                     'product_id': line.product_id.id,
#                     'product_uom': line.uom_id.id,
#                     'product_uom_qty': line.quantity,
#                     'picking_id': picking.id,
#                     'location_id': requisition.source_location_id.id,
#                     'location_dest_id': requisition.destination_location_id.id,
#                 }
#                 self.env['stock.move'].create(move_vals)
            
#             requisition.internal_transfer_id = picking.id
#             requisition.state = 'ready_for_transfer'
            
#             # Confirm the transfer
#             picking.action_confirm()
            
#             # requisition.message_post(
#             #     body=_("Internal transfer created: %s") % picking.name,
#             #     subject=_("Transfer Created")
#             # )
#         return True
            
#     def action_request_to_another_location(self):
#         """Request products from another location - Only inventory users"""
#         for requisition in self:
#             if requisition.state != 'submitted':
#                 raise UserError(_("Only submitted requisition can be requested from other locations."))
            
#             if not requisition._check_inventory_user_permission():
#                 raise UserError(_("Only inventory users can request from other locations."))
            
#             if not requisition.requested_location_id:
#                 raise UserError(_("Please select a location to request from."))
            
#             requisition.state = 'requested_other_location'
#         return True
            
#             # # Log the request
#             # requisition.message_post(
#             #     body=_("Products requested from location: %s to %s") % (
#             #         requisition.requested_location_id.name, 
#             #         requisition.destination_location_id.name
#             #     ),
#             #     subject=_("Requested Another Location")
#             # )
    
#     # def action_set_draft(self):
#     #     """Reset to draft - Only original requester or inventory users can reset"""
#     #     for requisition in self:
#     #         can_reset = (
#     #             (requisition.state == 'draft' and requisition.requested_by == self.env.user) or
#     #             (requisition.state == 'submitted' and self.env.user.has_group('stock.group_stock_manager'))
#     #         )
            
#     #         if not can_reset:
#     #             raise UserError(_("You don't have permission to reset this requisition."))
            
#     #         requisition.state = 'draft'
#     #         requisition.message_post(
#     #             body=_("Requisition reset to draft."),
#     #             subject=_("Reset to Draft")
#     #         )

#     def action_set_draft(self):
#         """Reset to draft - Only original requester, inventory users, or admin can reset"""
#         for requisition in self:
#             is_admin = self.env.user.has_group('dw_stock_requisition.group_manufacturing_requisition_admin')
#             can_reset = (
#                 is_admin or
#                 (requisition.state == 'draft' and requisition.requested_by == self.env.user) or
#                 (requisition.state == 'submitted' and self.env.user.has_group('dw_stock_requisition.group_inventory_team'))
#             )
            
#             if not can_reset:
#                 raise UserError(_("You don't have permission to reset this requisition."))
            
#             requisition.state = 'draft'
#             requisition.message_post(
#                 body=_("Requisition reset to draft."),
#                 subject=_("Reset to Draft")
#             )