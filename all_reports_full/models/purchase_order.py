from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    other_references = fields.Char(string="Other References")
    dispatched_through = fields.Char(string="Dispatched through")
    destination = fields.Char(string="Destination")
    terms_of_delivery = fields.Char(string="Terms of Delivery")
