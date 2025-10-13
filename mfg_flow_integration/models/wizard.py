from odoo import api, fields, models
from odoo.exceptions import UserError

class ManufactureOrPurchaseWizard(models.TransientModel):
    _name = 'manufacture.or.purchase.wizard'
    _description = 'Manufacture or Purchase Selection Wizard'

    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    warning_message = fields.Text(string="Stock Message", readonly=True)
    action_type = fields.Selection([
        ('manufacture', 'Create Manufacturing Order'),
        ('purchase', 'Create Purchase Order'),
    ], string="Action", required=False)

    def action_proceed(self):
        self.ensure_one()
        order = self.sale_order_id

        if not self.action_type:
            raise UserError("Please select an action (Manufacture or Purchase).")

        if self.action_type == 'manufacture':
            return self._create_manufacturing_orders(order)
        elif self.action_type == 'purchase':
            return self._open_purchase_order_form(order)

    def _create_manufacturing_orders(self, order):
        """Create Manufacturing Orders for all order lines"""
        for line in order.order_line:
            product = line.product_id
            bom = product.bom_ids[:1]
            if not bom:
                raise UserError(f"No Bill of Materials found for product {product.display_name}.")
            
            self.env['mrp.production'].create({
                'product_id': product.id,
                'product_qty': line.product_uom_qty,
                'product_uom_id': line.product_uom.id,
                'bom_id': bom.id,
                'origin': order.name,
            })
        
        return {'type': 'ir.actions.act_window_close'}

    def _open_purchase_order_form(self, order):
        """Open Purchase Order form with pre-filled order lines in context"""
        # Prepare order lines data for context
        po_lines = []
        
        for line in order.order_line:
            product = line.product_id
            
            # Get supplier info if available
            supplierinfo = product.seller_ids[:1]
            price = supplierinfo.price if supplierinfo else product.standard_price
            
            po_lines.append({
                'product_id': product.id,
                'name': product.display_name,
                'product_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
                'price_unit': price,
                'date_planned': fields.Datetime.now(),
            })
        
        # Open new Purchase Order form with lines in context
        return {
            'name': 'Create Purchase Order',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
            'context': {
                'default_origin': order.name,
                'default_order_line': [(0, 0, line) for line in po_lines],
            }
        }







# from odoo import api, fields, models
# from odoo.exceptions import UserError

# class ManufactureOrPurchaseWizard(models.TransientModel):
#     _name = 'manufacture.or.purchase.wizard'
#     _description = 'Manufacture or Purchase Selection Wizard'

#     sale_order_id = fields.Many2one('sale.order', string="Sale Order")
#     warning_message = fields.Text(string="Stock Message", readonly=True)
#     action_type = fields.Selection([
#         ('manufacture', 'Create Manufacturing Order'),
#         ('purchase', 'Create Purchase Order'),
#     ], string="Action", required=False)

#     def action_proceed(self):
#         self.ensure_one()
#         order = self.sale_order_id

#         if not self.action_type:
#             raise UserError("Please select an action (Manufacture or Purchase).")

#         if self.action_type == 'manufacture':
#             return self._create_manufacturing_orders(order)
#         elif self.action_type == 'purchase':
#             return self._create_purchase_order(order)

#     def _create_manufacturing_orders(self, order):
#         """Create Manufacturing Orders for all order lines"""
#         for line in order.order_line:
#             product = line.product_id
#             bom = product.bom_ids[:1]
#             if not bom:
#                 raise UserError(f"No Bill of Materials found for product {product.display_name}.")
            
#             self.env['mrp.production'].create({
#                 'product_id': product.id,
#                 'product_qty': line.product_uom_qty,
#                 'product_uom_id': line.product_uom.id,
#                 'bom_id': bom.id,
#                 'origin': order.name,
#             })
        
#         return {'type': 'ir.actions.act_window_close'}

#     def _create_purchase_order(self, order):
#         """Create Purchase Order and open form view for vendor selection"""
#         # Collect all products that need to be purchased
#         po_lines = []
        
#         for line in order.order_line:
#             product = line.product_id
            
#             # Get supplier info if available (optional)
#             supplierinfo = product.seller_ids[:1]
#             price = supplierinfo.price if supplierinfo else product.standard_price
            
#             po_lines.append((0, 0, {
#                 'product_id': product.id,
#                 'name': product.display_name,
#                 'product_qty': line.product_uom_qty,
#                 'product_uom': line.product_uom.id,
#                 'price_unit': price,
#                 'date_planned': fields.Datetime.now(),
#             }))
        
#         # Create Purchase Order without vendor (user will select it)
#         purchase_order = self.env['purchase.order'].create({
#             'origin': order.name,
#             'order_line': po_lines,
#         })
        
#         # Open the Purchase Order form view
#         return {
#             'name': 'Purchase Order',
#             'type': 'ir.actions.act_window',
#             'res_model': 'purchase.order',
#             'res_id': purchase_order.id,
#             'view_mode': 'form',
#             'view_type': 'form',
#             'target': 'current',
#         }















# from odoo import api, fields, models
# from odoo.exceptions import UserError

# class ManufactureOrPurchaseWizard(models.TransientModel):
#     _name = 'manufacture.or.purchase.wizard'
#     _description = 'Manufacture or Purchase Selection Wizard'

#     sale_order_id = fields.Many2one('sale.order', string="Sale Order")
#     warning_message = fields.Text(string="Stock Message", readonly=True)
#     action_type = fields.Selection([
#         ('manufacture', 'Create Manufacturing Order'),
#         ('purchase', 'Create Purchase Order'),
#     ], string="Action", required=False)

#     def action_proceed(self):
#         self.ensure_one()
#         order = self.sale_order_id

#         if not self.action_type:
#             raise UserError("Please select an action (Manufacture or Purchase).")

#         for line in order.order_line:
#             product = line.product_id

#             # --- Manufacturing Path ---
#             if self.action_type == 'manufacture':
#                 bom = product.bom_ids[:1]
#                 if not bom:
#                     raise UserError(f"No Bill of Materials found for product {product.display_name}.")
#                 self.env['mrp.production'].create({
#                     'product_id': product.id,
#                     'product_qty': line.product_uom_qty,
#                     'product_uom_id': line.product_uom.id,
#                     'bom_id': bom.id,
#                     'origin': order.name,
#                 })

#             # --- Purchase Path ---
#             elif self.action_type == 'purchase':
#                 supplierinfo = product.seller_ids[:1]
#                 if not supplierinfo:
#                     raise UserError(f"No vendor found for product {product.display_name}. Please define at least one vendor.")
                
#                 vendor = supplierinfo.partner_id

#                 purchase_order = self.env['purchase.order'].create({
#                     'partner_id': vendor.id,
#                     'origin': order.name,
#                 })
#                 self.env['purchase.order.line'].create({
#                     'order_id': purchase_order.id,
#                     'product_id': product.id,
#                     'name': product.display_name,
#                     'product_qty': line.product_uom_qty,
#                     'product_uom': line.product_uom.id,
#                     'price_unit': supplierinfo.price or product.standard_price,
#                     'date_planned': fields.Datetime.now(),
#                 })
#         return {'type': 'ir.actions.act_window_close'}





















# from odoo import api, fields, models
# from odoo.exceptions import UserError

# class ManufactureOrPurchaseWizard(models.TransientModel):
#     _name = 'manufacture.or.purchase.wizard'
#     _description = 'Manufacture or Purchase Selection Wizard'

#     sale_order_id = fields.Many2one('sale.order', string="Sale Order")
#     action_type = fields.Selection([
#         ('manufacture', 'Create Manufacturing Order'),
#         ('purchase', 'Create Purchase Order'),
#     ], string="Action", required=True)

#     def action_proceed(self):
#         self.ensure_one()
#         order = self.sale_order_id

#         for line in order.order_line:
#             product = line.product_id

#             # --- Manufacturing Path ---
#             if self.action_type == 'manufacture':
#                 bom = product.bom_ids[:1]
#                 if not bom:
#                     raise UserError(f"No Bill of Materials found for product {product.display_name}.")
#                 self.env['mrp.production'].create({
#                     'product_id': product.id,
#                     'product_qty': line.product_uom_qty,
#                     'product_uom_id': line.product_uom.id,
#                     'bom_id': bom.id,
#                     'origin': order.name,
#                 })

#             # --- Purchase Path ---
#             elif self.action_type == 'purchase':
#                 supplierinfo = product.seller_ids[:1]
#                 if not supplierinfo:
#                     raise UserError(f"No vendor found for product {product.display_name}. Please define at least one vendor.")
                
#                 vendor = supplierinfo.partner_id

#                 purchase_order = self.env['purchase.order'].create({
#                     'partner_id': vendor.id,
#                     'origin': order.name,
#                 })
#                 self.env['purchase.order.line'].create({
#                     'order_id': purchase_order.id,
#                     'product_id': product.id,
#                     'name': product.display_name,
#                     'product_qty': line.product_uom_qty,
#                     'product_uom': line.product_uom.id,
#                     'price_unit': supplierinfo.price or product.standard_price,
#                     'date_planned': fields.Datetime.now(),
#                 })
#         return {'type': 'ir.actions.act_window_close'}
