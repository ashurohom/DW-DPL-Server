from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # lead_seq = fields.Char(
    #     string='Lead Number',
    #     related='opportunity_id.lead_seq',
    #     readonly=True
    # )
