from odoo import models, fields, api
from datetime import datetime
from odoo.fields import Datetime as OdooDatetime
import pytz

class DepartmentTimeTracking(models.Model):
    _name = 'department.time.tracking'
    _description = 'Department Time Tracking for CRM'

    # Link to CRM Lead (for now)
    target_model = fields.Reference(selection=[('crm.lead', 'CRM Lead')], string='Target')


    stage_name = fields.Char("Stage / State")

    user_id = fields.Many2one(
        'res.users', string="Responsible User", default=lambda self: self.env.user
    )
    employee_id = fields.Many2one('hr.employee', string="Responsible Employee")

    start_time = fields.Datetime(string='Start Time', default=fields.Datetime.now)
    end_time = fields.Datetime(string='End Time')
    duration = fields.Float(string='Duration (hours)', compute='_compute_duration', store=True)

    status = fields.Selection([
        ('in_progress', 'In Progress'),
        ('done', 'Done')
    ], string='Status', default='in_progress')

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for rec in self:
            start = rec.start_time
            end = rec.end_time or fields.Datetime.now()  # handle ongoing stages
            if start:
                if isinstance(start, str):
                    start = fields.Datetime.from_string(start)
                if isinstance(end, str):
                    end = fields.Datetime.from_string(end)
                delta = end - start
                rec.duration = delta.total_seconds() / 3600
            else:
                rec.duration = 0

