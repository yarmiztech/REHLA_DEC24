from odoo import fields,models,api
from datetime import datetime,date
from dateutil.relativedelta import relativedelta


class JsonConfiguration(models.Model):
    _name = 'json.configuration'


    def default_cron_job_id(self):
        return self.env['ir.cron'].search([('name','=','Invoice Creation Automatic')])
    name = fields.Char('Sale Link',required=1)
    cron_job_id = fields.Many2one('ir.cron',default=default_cron_job_id)
    interval_number = fields.Integer(default=1, help="Repeat every x.")
    interval_type = fields.Selection([('minutes', 'Minutes'),
                                      ('hours', 'Hours'),
                                      ('days', 'Days'),
                                      ('weeks', 'Weeks'),
                                      ('months', 'Months')], string='Interval Unit', default='months')

    def update_values(self):
        self.sudo().cron_job_id.interval_number = self.interval_number
        self.sudo().cron_job_id.interval_type = self.interval_type
        if self.interval_type == 'minutes':
            self.sudo().cron_job_id.nextcall = datetime.now() + relativedelta(minutes=self.interval_number)
        if self.interval_type == 'hours':
            self.sudo().cron_job_id.nextcall = datetime.now() + relativedelta(hours=self.interval_number)
        if self.interval_type == 'days':
            self.sudo().cron_job_id.nextcall = datetime.now() + relativedelta(days=self.interval_number)
        if self.interval_type == 'weeks':
            self.sudo().cron_job_id.nextcall = datetime.now() + relativedelta(weeks=self.interval_number)
        if self.interval_type == 'months':
            self.sudo().cron_job_id.nextcall = datetime.now() + relativedelta(months=self.interval_number)

    @api.onchange('cron_job_id')
    def compute_values(self):
        self.sudo().interval_number = self.sudo().cron_job_id.interval_number
        self.sudo().interval_type = self.sudo().cron_job_id.interval_type
class JsonPaymnetConfiguration(models.Model):
    _name = 'json.payment.configuration'


    def default_cron_job_id(self):
        return self.env['ir.cron'].search([('name','=','Rehla Payments Automatic')])
    name = fields.Char('Payment Link',required=1)
    cron_job_id = fields.Many2one('ir.cron',default=default_cron_job_id)
    # cron_job_id = fields.Many2one('ir.cron')
    interval_number = fields.Integer(default=1, help="Repeat every x.")
    interval_type = fields.Selection([('minutes', 'Minutes'),
                                      ('hours', 'Hours'),
                                      ('days', 'Days'),
                                      ('weeks', 'Weeks'),
                                      ('months', 'Months')], string='Interval Unit', default='months')

    def update_values(self):
        self.sudo().cron_job_id.interval_number = self.interval_number
        self.sudo().cron_job_id.interval_type = self.interval_type
        if self.interval_type == 'minutes':
            self.sudo().cron_job_id.nextcall = datetime.now() + relativedelta(minutes=self.interval_number)
        if self.interval_type == 'hours':
            self.sudo().cron_job_id.nextcall = datetime.now() + relativedelta(hours=self.interval_number)
        if self.interval_type == 'days':
            self.sudo().cron_job_id.nextcall = datetime.now() + relativedelta(days=self.interval_number)
        if self.interval_type == 'weeks':
            self.sudo().cron_job_id.nextcall = datetime.now() + relativedelta(weeks=self.interval_number)
        if self.interval_type == 'months':
            self.sudo().cron_job_id.nextcall = datetime.now() + relativedelta(months=self.interval_number)

    @api.onchange('cron_job_id')
    def compute_values(self):
        self.sudo().interval_number = self.sudo().cron_job_id.interval_number
        self.sudo().interval_type = self.sudo().cron_job_id.interval_type


class TransactionReport(models.Model):
    _name = 'transaction.report'
    _order = 'id desc'

    rehla_id = fields.Integer(string='Rehla Id')
    trip_id = fields.Integer(string="Trip Id")
    reservation_id = fields.Char(String="ReservationId")
    vat_amount = fields.Integer(string="Vat Amount")
    reh_driver_id = fields.Integer(string='Driver Id')
    driver_name = fields.Many2one('res.partner')
    identity_number = fields.Char(string="IdentityNumber")
    email = fields.Char(string='Email')
    mobile = fields.Char(string='PhoneNumber')
    amount = fields.Integer(string='Amount')
    create_date = fields.Date(string="Date")
