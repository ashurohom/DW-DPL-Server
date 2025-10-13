from odoo import models, fields, api
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    qc_state = fields.Selection([
        ('not_required', 'Not Required'),
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ], string='QC State', default='not_required', compute='_compute_qc_state', store=True)


    def action_send_for_qc(self):
        for picking in self:
            if picking.picking_type_id.code != 'incoming':
                raise UserError('Quality check can only be performed for incoming shipments.')

            existing_qc = self.env['dw.quality.check'].search([('picking_id', '=', picking.id)])
            if existing_qc:
                raise UserError('Quality check already initiated for this receipt.')

            # Create QC records for each product in the receipt
            for move in picking.move_ids_without_package:
                qty_done = sum(move.move_line_ids.mapped('quantity'))
                if qty_done <= 0:
                    continue  # Skip if nothing was actually received
                self.env['dw.quality.check'].create({
                    'picking_id': picking.id,
                    'product_id': move.product_id.id,
                    'quantity': qty_done,
                })

            picking.message_post(body="Quality Check initiated for this receipt.")
            picking.qc_state = 'pending'

        return {
            'type': 'ir.actions.act_window',
            'name': 'Quality Checks',
            'res_model': 'dw.quality.check',
            'view_mode': 'tree,form',
            'domain': [('picking_id', '=', self.id)],
            'target': 'current',
        }


    def action_done(self):
        # prevent validation if QC failed or pending depending on your policy
        for picking in self:
            if picking.picking_type_id.code == 'incoming':
                if picking.qc_state == 'failed':
                    raise UserError('QC failed for this receipt. Please resolve QC before validating the transfer.')
                if picking.qc_state == 'pending':
                    # Option: block; here we block by default
                    raise UserError('QC is pending for this receipt. Please perform QC before validating the transfer.')
        return super().action_done()
    
    def action_set_failed(self):
        for rec in self:
            rec.status = 'failed'
            rec.passed = False
            rec._update_picking_qc_state()
            rec.message_post(body=f'QC {rec.name} marked as Failed by {self.env.user.name}')
            rec._create_return_request()

    def _create_return_request(self):
        """Automatically create a return picking when QC fails."""
        for rec in self:
            if not rec.picking_id:
                continue
            picking = rec.picking_id
            return_picking_type = picking.picking_type_id.return_picking_type_id or picking.picking_type_id
            if not return_picking_type:
                raise UserError('No return operation type configured for this picking type.')

            return_picking = picking.copy({
                'origin': f"Return for {picking.name} (QC Failed)",
                'picking_type_id': return_picking_type.id,
                'move_ids_without_package': [],
            })
            # create return move for defective product
            self.env['stock.move'].create({
                'name': f'Return {rec.product_id.display_name}',
                'product_id': rec.product_id.id,
                'product_uom_qty': rec.quantity,
                'product_uom': rec.product_id.uom_id.id,
                'picking_id': return_picking.id,
                'location_id': picking.location_dest_id.id,
                'location_dest_id': picking.location_id.id,
            })
            return_picking.action_confirm()
            picking.message_post(body=f'Return {return_picking.name} created for failed QC {rec.name}.')



    @api.depends('move_ids_without_package.move_line_ids.quantity')
    def _compute_qc_state(self):
        for picking in self:
            if picking.picking_type_id.code != 'incoming':
                picking.qc_state = 'not_required'
                continue

            qc_records = self.env['dw.quality.check'].search([('picking_id', '=', picking.id)])
            if not qc_records:
                picking.qc_state = 'not_required'
            elif all(rec.status == 'passed' for rec in qc_records):
                picking.qc_state = 'passed'
            elif any(rec.status == 'failed' for rec in qc_records):
                picking.qc_state = 'failed'
            else:
                picking.qc_state = 'pending'
