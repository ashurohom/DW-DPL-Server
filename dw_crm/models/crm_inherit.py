from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    department_times = fields.One2many('crm.lead.time', 'lead_id', string='Department Time Tracking')
    # engineering_team_id = fields.Many2one(
    #     'res.users', 
    #     string="Engineering Team",
    #     help="Assign the lead to an Engineering team member."
    # )

       
    def action_send_to_analysis(self):
        """Transition from 'New' to 'Send for Analysis' stage."""
        send_stage = self.env.ref('dw_crm.stage_send_for_analysis', raise_if_not_found=False)
        if not send_stage:
            raise UserError("Stage 'Send for Analysis' not found. Please install CRM stages data.")
        self.write({'stage_id': send_stage.id})
        self.message_post(body="Lead sent to analysis by %s." % self.env.user.name)
        return True  # Triggers form refresh

    def action_analysis_done(self):
        """Transition from 'Send for Analysis' to 'Analysis Done' stage."""
        done_stage = self.env.ref('dw_crm.stage_analysis_done', raise_if_not_found=False)
        if not done_stage:
            raise UserError("Stage 'Analysis Done' not found. Please install CRM stages data.")
        self.write({'stage_id': done_stage.id})
        self.message_post(body="Analysis completed by %s." % self.env.user.name)
        return True  # Triggers form refresh
    
    def action_send_quotation(self):
        """Transition from 'Analysis Done' to 'Quotation Sent' stage."""
        quotation_stage = self.env.ref('dw_crm.stage_quotation_sent', raise_if_not_found=False)
        if not quotation_stage:
            raise UserError("Stage 'Quotation Sent' not found. Please install CRM stages data.")
        self.write({'stage_id': quotation_stage.id})
        self.message_post(body="Quotation sent for this lead by %s." % self.env.user.name)
        return True  # Triggers form refresh
    
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(CrmLead, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            ctx = self.env.context.copy()
            for record in self:
                if record.stage_id.name != 'Analysis Done':
                    ctx['hide_new_quotation'] = True
                    ctx['hide_send_quotation'] = True
                else:
                    ctx['hide_new_quotation'] = False
                    ctx['hide_send_quotation'] = False
            res['context'] = ctx
        return res


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    allowed_group_ids = fields.Many2many(
                            'res.groups',
                            string="Allowed Groups",
                            help="Only users in these groups can move a lead into this stage."
                        )

    @api.model
    def create_default_stages(self):
        # """Ensure Sales Department has custom stages."""
        # team = self.env['crm.team'].search([('name', '=', 'Sales Department')], limit=1)
        # if not team:
        #     team = self.env['crm.team'].create({'name': 'Sales Department'})

        stage_data = [
            {'name': 'New', 'sequence': 1, 'fold': False},
            {'name': 'Send for Analysis', 'sequence': 2, 'fold': False},
            {'name': 'Analysis Done', 'sequence': 3, 'fold': False},
            {'name': 'Quotation Sent', 'sequence': 4, 'fold': False},
            {'name': 'Won', 'sequence': 5, 'fold': True, 'is_won': True},
        ]

        # for data in stage_data:
        #     exists = self.search([
        #         ('name', '=', data['name']),
        #         ('team_id', '=', team.id)
        #     ], limit=1)
        #     if not exists:
        #         self.create({**data, 'team_id': False})


    

