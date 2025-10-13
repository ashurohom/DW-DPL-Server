# from odoo import api, models

# class SaleOrder(models.Model):
#     _inherit = "sale.order"

#     def action_confirm(self):
#         res = super().action_confirm()
#         for order in self:
#             for line in order.order_line:
#                 if line.product_id.type == 'product' and line.product_id.bom_ids:
#                     bom = line.product_id.bom_ids and line.product_id.bom_ids[0] or False
#                     if bom:
#                         self.env['mrp.production'].create({
#                             'product_id': line.product_id.id,
#                             'product_qty': line.product_uom_qty,
#                             'product_uom_id': line.product_uom.id,
#                             'bom_id': bom.id,
#                             'origin': order.name,
#                         })
#         return res


# from odoo import api, models

# class SaleOrder(models.Model):
#     _inherit = "sale.order"

#     def action_confirm(self):
#         res = super().action_confirm()

#         # Open wizard for user choice
#         return {
#             'name': 'Select Action',
#             'type': 'ir.actions.act_window',
#             'res_model': 'manufacture.or.purchase.wizard',
#             'view_mode': 'form',
#             'target': 'new',
#             'context': {'default_sale_order_id': self.id},
#         }


from odoo import api, models, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        self.ensure_one()
        StockQuant = self.env['stock.quant']

        unavailable_products = []
        for line in self.order_line.filtered(lambda l: l.product_id.type == 'product'):
            qty_available = StockQuant._get_available_quantity(
                line.product_id, self.warehouse_id.lot_stock_id)
            if qty_available < line.product_uom_qty:
                unavailable_products.append(line.product_id.display_name)

        # 🟥 If stock not available → Open wizard
        if unavailable_products:
            message = _("The following products are not available in stock:\n- %s") % "\n- ".join(unavailable_products)
            return {
                'name': _('Product Not Available'),
                'type': 'ir.actions.act_window',
                'res_model': 'manufacture.or.purchase.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_sale_order_id': self.id,
                    'default_warning_message': message,
                },
            }

        # ✅ If stock available → Confirm the sale order and create delivery
        res = super(SaleOrder, self).action_confirm()

        # Ensure sale order state changes to 'sale'
        self.state = 'sale'

        # ✅ Show success notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Stock Available'),
                'message': _('All products are available in stock. The order has been confirmed and delivery order created.'),
                'sticky': False,
                'type': 'success',
            }
        }
