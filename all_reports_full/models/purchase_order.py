from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    other_references = fields.Char(string="Other References")
    dispatched_through = fields.Char(string="Dispatched through")
    destination = fields.Char(string="Destination")
    terms_of_delivery = fields.Char(string="Terms of Delivery")

    ship_to_address = fields.Text(
        string="Ship To",
        help="Consignee / Ship To Address"
    )

    ship_to_name = fields.Char(string="Ship To Name")
    ship_to_street = fields.Char(string="Address Line 1")
    ship_to_street2 = fields.Char(string="Address Line 2")
    ship_to_city = fields.Char(string="City")
    ship_to_state_id = fields.Many2one('res.country.state', string="State")
    ship_to_zip = fields.Char(string="ZIP")
    ship_to_gstin = fields.Char(string="GSTIN/UIN")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        company = self.env.company

        res.setdefault('ship_to_name', company.name)
        res.setdefault('ship_to_street', company.street)
        res.setdefault('ship_to_street2', company.street2)
        res.setdefault('ship_to_city', company.city)
        res.setdefault('ship_to_state_id', company.state_id.id if company.state_id else False)
        res.setdefault('ship_to_zip', company.zip)
        res.setdefault('ship_to_gstin', company.vat)

        return res
    


    commercial_terms = fields.Html(
        string="Commercial Terms & Conditions",
        help="Annex-1 Commercial Terms and Conditions",
        default="""
        <h3 style="text-align:center;"><strong>Annex-1</strong></h3>
        <h3 style="text-align:center;"><strong>COMMERCIAL TERMS AND CONDITIONS</strong></h3>

        <p><strong><u>1. ORDER ACCEPTANCE</u></strong></p>
        <p>
        1.1 Kindly send us your Order Acceptance within 2 working days of receipt of this Purchase Order.<br/>
        If we do not receive your Order Acceptance within the mentioned period,<br/>
        this Purchase Order and the Terms and Conditions mentioned herein<br/>
        shall be deemed unconditionally accepted by you.
        </p>

        <p><strong><u>2. PRICE BASIS</u></strong></p>
        <p>2.1 The above prices are Ex Your Works.</p>
        <p>2.2 Currency shall be Indian Rupees.</p>
        <p>
        2.3 The above prices will remain firm and final till the complete execution
        of supplies of the entire material against the PO.
        </p>

        <p><strong><u>3. TRANSIT INSURANCE</u></strong></p>
        <p>3.1 It’s Vendor Responsibility.</p>

        <p><strong><u>4. L.D. CLAUSE FOR DELAY IN DELIVERY</u></strong></p>
        <p>
        4.1 L.D. clause at 5% from agreed date of delivery for 2 weeks delay,
        10% from 2 weeks to 4 weeks delay and 20% for further delay,
        in case you do not supply material on or before above-mentioned date.
        </p>

        <p><strong><u>5. DRAWING & DOCUMENTS TO BE FURNISHED FOR APPROVAL OF PURCHASER</u></strong></p>
        <p>5.1 Datasheets duly filled up.</p>
        <p>5.2 G.A Drawing with complete dimensions, shipping weight etc.</p>
        <p>5.3 QAP.</p>
        <p>5.4 Manufacturing Schedule.</p>
        <p>5.5 Billing Break up.</p>
        <p>5.6 Material Test Certificate / PDI reports.</p>

        <p><strong><u>6. RISK PURCHASE CLAUSE</u></strong></p>
        <p>
        6.1 DPL is at its sole liberty to purchase similar equipment for the purpose intended
        while ordering this material on you from any other source whether indigenous or foreign,
        at the risk and cost of the supplier in case:
        </p>
        <p>6.1.1 Supplier fails to start execution within the accepted delivery schedule.</p>
        <p>6.1.2 Manufacturing progress is not sufficient to meet delivery schedule.</p>
        <p>6.1.3 Material does not meet specification, quality, or aesthetics.</p>
        <p>6.1.4 Delay in supplies partially or fully.</p>
        <p>6.1.5 Supplied item does not conform to approved documents.</p>
        <p>6.1.6 Supplied items are not suitable for intended purpose.</p>
        <p>6.1.7 Supplier will be given opportunity to remedy before action.</p>

        <p><strong><u>7. REJECTION OF MATERIALS</u></strong></p>
        <p>
        7.1 Rejected materials shall be taken back by supplier at their own cost and risk.
        DPL shall not be liable for shortages or deterioration.
        </p>

        <p><strong><u>8. GUARANTEES & LIABILITY</u></strong></p>
        <p>
        8.1 Supplier guarantees that supplies comply with specifications and applicable laws.
        Defective supplies shall be replaced at supplier’s cost.
        </p>
        <p>
        8.2 Warranty, guarantee certificate and product manuals shall be submitted with machinery.
        </p>

        <p><strong><u>9. INVOICE, CHALLAN & TRANSIT DOCUMENTS</u></strong></p>
        <p>
        9.1 Invoices, challan, inspection and test certificates shall accompany the consignment.
        </p>
        <p>
        9.2 PO number, revision number and item code must be quoted on documents.
        </p>
        <p>
        9.3 Material shall be dispatched only after clearance from Duisport Packing India Pvt. Ltd.
        </p>

        <p><strong><u>10. QUALITY PARAMETERS</u></strong></p>
        <p>10.1 No rust on stainless steel or iron parts.</p>
        <p>10.2 Painting must be proper without spot marks.</p>
        <p>10.3 Final rates based on actual measurement verified by DPL.</p>
        <p>10.4 Quality of all items must be ensured.</p>
        <p>10.5 Soundproofing and insulation quality must be ensured.</p>
        <p>10.6 Hardware quality must be galvanized.</p>

        <p><strong><u>11. DISPUTES / ARBITRATION</u></strong></p>
        <p>
        11.1 Disputes shall be resolved through arbitration as per Arbitration & Conciliation Act, 2015.
        </p>
        <p>11.2 Place of arbitration shall be Pune, India.</p>
        <p>11.3 All disputes subject to Pune jurisdiction.</p>

        <p><strong><u>12. FORCE MAJEURE</u></strong></p>
        <p>
        Delivery period shall be extended for events like war, flood, fire, epidemic, or acts of God.
        Supplier must provide documentary evidence.
        </p>

        <p><strong><u>13. GENERAL</u></strong></p>
        <p>
        13.1 Terms & conditions mentioned above shall prevail unless otherwise stated in the PO.
        </p>
        """
    )
