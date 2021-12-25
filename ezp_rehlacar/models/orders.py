# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime
from datetime import date
import time
import fcntl
import socket
import struct
import macpath
from uuid import getnode as get_mac
from odoo.exceptions import UserError, ValidationError


class ProfitCarOrders(models.Model):
    _name = 'profit.car.orders'
    _order = 'id desc'

    rehla_id = fields.Integer('Rehla Id')
    trip_id = fields.Integer('Trip Id')
    passenger_id = fields.Integer('Passenger Id')
    passenger = fields.Many2one('res.partner', string='Passenger')
    driver = fields.Many2one('res.partner', string='Driver')
    reh_driver_id = fields.Integer('Driver Id')
    trip_cost = fields.Float('TripCost')
    tax_amount = fields.Float('Tax Amount')
    driver_cost = fields.Float('Driver Cost')
    profit = fields.Float('Profit')
    date = fields.Date('Date')
    revenue_profit = fields.Float('Revenue Profit')


class WalletAmount(models.Model):
    _name = 'wallet.amount'
    _order = 'id desc'

    rehla_id = fields.Integer('Rehla Id')
    trip_id = fields.Integer('Trip Id')
    passenger_id = fields.Integer('Passenger Id')
    reh_driver_id = fields.Integer('Driver Id')
    passenger = fields.Many2one('res.partner', string='Passenger Name')
    driver_id = fields.Many2one('res.partner', string='Driver Name')
    trip_cost = fields.Float('TripCost')
    # tax_amount = fields.Float('Tax Amount')
    driver_cost = fields.Float('Driver Cost')
    date = fields.Date('Date')
    payment_type = fields.Selection([
        ('True', 'cash'),
        ('False', 'Wallet'),

    ], string='PaymentType', readonly=True, copy=False, index=True, track_visibility='onchange',
        track_sequence=3,
    )
    wallet_amount = fields.Float(string='Wallet Amount')


class WalletAmountReport(models.Model):
    _name = 'wallet.amount.report'
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    payment_type = fields.Selection([
        ('True', 'cash'),
        ('False', 'Wallet'),

    ], string='PaymentType', default='True', copy=False, index=True, track_visibility='onchange',
        track_sequence=3,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),

    ], string='Status', default='draft', readonly=True, copy=False, index=True, track_visibility='onchange',
        track_sequence=3,
    )
    driver_id = fields.Many2one('res.partner', string='Driver', domain=[('reh_driver_id', '!=', 0)])
    from_date = fields.Date('From Date', default=fields.Date.context_today)
    to_date = fields.Date('To Date', default=fields.Date.context_today)
    all_lines = fields.One2many('wallet.amount.report.lines', 'wallet_repo_id')
    paying_amount =fields.Float(string='Paying Amount')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'wallet.amount.report') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('wallet.amount.report') or _('New')
        return super(WalletAmountReport, self).create(vals)

    def wallet_amount_pay(self):
        if self.driver_id:
        # for line in self.all_lines:
            vals = {
                'journal_id': self.env['account.journal'].search(
                    [('name', '=', 'Miscellaneous Operations'),
                     ('company_id', '=', 1)]).id,
                'state': 'draft',
                'ref': self.driver_id.name
            }
            pay_id_list = []
            move_id = self.env['account.move'].create(vals)
            partner_id = self.driver_id.id
            label =self.driver_id.name

            # if self.type_of_credit == False:
            temp = (0, 0, {
                'account_id': self.env['account.account'].sudo().search(
                    [('name', '=', 'Creditors'),
                     ('company_id', '=', 1)]).id,
                'name': label,
                'move_id': move_id.id,
                'date': datetime.today().date(),
                'partner_id': self.driver_id.id,
                'debit': 0,
                # 'credit': line.wallet_amount,
                'credit': self.paying_amount,
            })
            pay_id_list.append(temp)

            acc = self.env['account.account'].sudo().search(
                [('name', '=', 'Purchase Expense'),
                 ('company_id', '=', 1)])
            temp = (0, 0, {
                'account_id': acc.id,
                'name': label,
                'move_id': move_id.id,
                'date': datetime.today().date(),
                'partner_id': self.driver_id.id,
                'debit': self.paying_amount,
                'credit': 0,
            })
            pay_id_list.append(temp)
            move_id.line_ids = pay_id_list
            move_id.sudo().action_post()
        self.write({'state': 'paid'})

    @api.onchange('from_date', 'to_date', 'driver_id', 'payment_type')
    def onchange_from_date(self):
        self.all_lines = False
        if self.driver_id:
            total = self.env['wallet.amount'].search(
                [('driver_id', '=', self.driver_id.id), ('payment_type', '=', self.payment_type),
                 ('date', '>=', self.from_date), ('date', '<=', self.to_date)])
        else:
            total = self.env['wallet.amount'].search(
                [('date', '>=', self.from_date), ('payment_type', '=', self.payment_type),
                 ('date', '<=', self.to_date)])

        invoice_list = []
        for each_invoice in total:
            product_line = (0, 0, {
                'passenger_id': each_invoice.passenger_id,
                'reh_driver_id': each_invoice.reh_driver_id,
                'passenger': each_invoice.passenger.id,
                'driver_id': each_invoice.driver_id.id,
                'trip_cost': each_invoice.trip_cost,
                'driver_cost': each_invoice.driver_cost,
                'date': each_invoice.date,
                'wallet_amount': each_invoice.wallet_amount

            })
            invoice_list.append(product_line)
        self.all_lines = invoice_list


class WalletAmountReportLines(models.Model):
    _name = 'wallet.amount.report.lines'
    _order = 'id desc'

    wallet_repo_id = fields.Many2one('wallet.amount.report')
    passenger_id = fields.Integer('Passenger Id')
    reh_driver_id = fields.Integer('Driver Id')
    passenger = fields.Many2one('res.partner', string='Passenger Name')
    driver_id = fields.Many2one('res.partner', string='Driver Name')
    trip_cost = fields.Float('TripCost')
    driver_cost = fields.Float('Driver Cost')
    date = fields.Date('Date')
    wallet_amount = fields.Float(string='Wallet Amount')



class SalesUpload(models.Model):
    _name = 'sales.upload'

    name = fields.Char(string='Reference', copy=False, default='New', readonly=True)



    def send_payment_transactions(self):
        print('fdgdfg')
        import json
        import requests
        from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
        if self.env['json.payment.configuration'].search([]):
            link = self.env['json.payment.configuration'].search([])[-1].name
            # responce = requests.get(link)
            if link:
                responce = requests.get(link)
                line_data = json.loads(responce.text)
                for each in line_data['model']:
                    print('Hello')
                    if not self.env['transaction.report'].sudo().search([('trip_id','=',each['TripId'])]):
                        invoice_date = each['CreationDate'].split('T')[0].split('-')
                        month = invoice_date[1]
                        day = invoice_date[2]
                        year = invoice_date[0]
                        vendor = self.env['res.partner'].sudo().search([('name','=',each['Name'])])
                        self.env['transaction.report'].sudo().create({
                            "rehla_id":each['Id'],
                            "trip_id":each['TripId'],
                            "reservation_id":each['ReservationId'],
                            "vat_amount":each['VATAmount'],
                            "reh_driver_id":each['IdentityNumber'],
                            "email":each['Email'],
                            "mobile":each['PhoneNumber'],
                            "amount":each['Amount'],
                            "driver_name":vendor[0].id,
                            "create_date": year + '-' + month + '-' + day,})
                        for each_inv in self.env['account.move'].sudo().search([('partner_id','=',vendor[0].id),('state','!=','cancel')]):

                            pmt_wizard = self.env['account.payment.register'].with_context(active_model='account.move',
                                                                                           active_ids=each_inv.ids).create({
                                'payment_date': year + '-' + month + '-' + day,
                                'journal_id': self.env['account.journal'].search(
                                    [('name', '=', 'Cash'), ('company_id', '=', 1)]).id,
                                'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                                'amount': each['Amount'],
                            })
                            pmt_wizard._create_payments()
                            print(pmt_wizard,vendor.name)
    def send_to_approval(self):

        import json
        import requests
        from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
        if self.env['json.configuration'].search([]):
            link = self.env['json.configuration'].search([])[-1].name
            responce = requests.get(link)
            print('dfdddgdfgdf111')
            if responce:

                if self.env['sale.order'].sudo().search([]):
                    last_trip = self.env['sale.order'].sudo().search([])[0].trip_id
                    print(last_trip, 'last_trip')
                    # "https: // apiv2.rehlacar.com / api / GetTripsReportForERP?LastTripId =%s" % last_trip
                    # responce = requests.get("https://apiv2.rehlacar.com/api/GetTripsReportForERP?LastTripId=%s" % last_trip)



                    # responce = requests.get("https://apiv2.rehlacar.com/api/GetTripsReportForERP?LastTripId=%s" % last_trip)
                    responce = requests.get(link.rsplit('=')[0]+"=%s" % last_trip)
                else:
                    # responce = requests.get("https://apiv2.rehlacar.com/api/GetTripsReportForERP?LastTripId=78940")
                    responce = requests.get(link)




                # responce = selfs.get("http://rehlaapi.native-tech.co/api/GetTripsReportForERP")
                #####################################3
                # responce = selfs.get("http://5.189.161.117:8069/Estimate/Orders?id=1")
                # line_data = json.loads(rec['data'])
                # current_u = http.self.env['ir.config_parameter'].get_param('web.base.url') + http.self.httpself.full_path
                # responce = selfs.get(self.httpself.__dict__['url'])
                if responce:
                    print('dfdddgdfgdf2222')
                    line_data = json.loads(responce.text)
                    # line_data = line_data['model']
                    order = self.env['sale.order']
                    line_data['model'].reverse()
                    i = 0
                    for each in line_data['model']:
                        # inb = self.env['account.move']
                        # inb1 = self.env['account.move']
                        # move_id = self.env['account.move']
                        print(each['TripCost'], 'Trip')
                        # if each['TripCost'] != '78941':
                        i = i + 1
                        if i <= 100:
                            inb = self.env['account.move']
                            inb1 = self.env['account.move']
                            move_id = self.env['account.move']
                            if each['DriverId']:
                                if not self.env['res.partner'].sudo().search([('reh_driver_id', '=', each['DriverId'])]):
                                    driver_id = self.env['res.partner'].sudo().create({
                                        'name': each['DriverName'],
                                        'reh_driver_id': each['DriverId'],
                                        'mobile': each['DriverPhoneNumber'],
                                        'email': each['DriverEmail'],
                                        'type_of_customer':'b_c',
                                        'schema_id':'IQA',
                                        'schema_id_no':'xxxx'
                                        # 'supplier':True

                                    })
                                else:
                                    driver_id = self.env['res.partner'].sudo().search(
                                        [('reh_driver_id', '=', each['DriverId'])])

                            if driver_id:
                                if not self.env['purchase.order'].sudo().search([('trip_id', '=', each['TripId'])]):
                                    product_p_line = []

                                    # tax_ids = self.env['account.tax'].search([('name', '=', 'VAT 15%'),('type_tax_use','=','purchase')])
                                    # tax_ids += self.env['account.tax'].search([('name', '=', 'Percentage 7%'),('type_tax_use','=','purchase')])

                                    excluded_value = 0
                                    basic_value = 0
                                    price_unit = 0

                                    transportation_aut = each['TransportAuthorityFee']
                                    airport_additional = each['AirportAdditionalFees']
                                    distance_amount = each['Distance'] * each['KMPrice']
                                    print(each['TripId'])
                                    actual = distance_amount + each['CaptainPounce'] + each['TransportAuthorityFee'] + each[
                                        'AirportAdditionalFees'] + each['MinimumPay']
                                    # 52.5###
                                    tax_value_system = actual * 7 / 100
                                    # 3.67####
                                    application_fee = tax_value_system
                                    coupon_value = each['CouponValue']
                                    actual_cali = actual + tax_value_system - each['CouponValue']
                                    value_added = actual_cali * 15 / 100

                                    trip_cost = each['TripCost'] - each['CouponValue']
                                    captain_cost = trip_cost - transportation_aut - airport_additional - tax_value_system + coupon_value - value_added
                                    price_unit = captain_cost

                                    # if tax_ids:
                                    #     tax = 0
                                    #     for eachs in tax_ids:
                                    #         if eachs.children_tax_ids:
                                    #             for ch in eachs.children_tax_ids:
                                    #                 tax += ch.amount
                                    #         else:
                                    #             tax += eachs.amount
                                    #     value = tax
                                    #     # basic_value = each['DriverRevenue'] * value / 100
                                    #     # basic_value1 = each['DriverRevenue'] - basic_value
                                    #     #
                                    #     # # line.basic_value = basic_value
                                    #     # # line.basic_value = basic_value
                                    #     #
                                    #     # # line.total_amount = line.quantity * line.amount
                                    #     # excluded_value = 1 * basic_value1
                                    #
                                    #     value = 100 + tax
                                    #     value = value
                                    #     basic_value = each['TripCost'] * 100 / value
                                    #     price_unit = basic_value / 1
                                    print(self.env['product.product'].sudo().search(
                                        [('name', '=', 'Driver Expense')]).id, 'product')

                                    print(self.env['uom.uom'].sudo().search([('name', '=', 'Units')]), 'UOMs')

                                    # line = (0, 0, {
                                    #     'product_id': self.env['product.product'].sudo().search(
                                    #         [('name', '=', 'Driver Expense')]).id,
                                    #     'product_qty': 1,
                                    #     'product_uom_qty': 1,
                                    #     'date_planned': datetime.now().date().strftime(DEFAULT_SERVER_DATE_FORMAT),
                                    #     # 'price_unit':each['DriverRevenue'],
                                    #     # 'price_unit':excluded_value,
                                    #     'price_unit':price_unit,
                                    #     'basic_value': basic_value,
                                    #     'trip_cost': each['DriverRevenue'],
                                    #     'display_type' :'line_section',
                                    #     # 'taxes_id':[(6, 0, tax_ids.ids)],
                                    #     'name': self.env['product.product'].sudo().search([('name', '=', 'Driver Expense')]).name,
                                    #     'product_uom': (self.env['uom.uom'].sudo().search([('name', '=', 'Units')])).id,
                                    #
                                    # })
                                    #
                                    #
                                    # product_p_line.append(line)

                                    po = self.env['purchase.order'].sudo().create({
                                        'partner_id': driver_id.id,
                                        'trip_id': each['TripId'],
                                        'transportation_aut': -transportation_aut,
                                        'airport_additional': -airport_additional,
                                        'taxvalue_system': -tax_value_system,
                                        'value_added': -value_added,
                                        'application_fee': -application_fee,
                                        'coupon_value': +coupon_value,
                                        # 'reh_driver_id':driver_id.reh_driver_id,
                                        'mobile': each['DriverPhoneNumber'],

                                        # 'rehla_id': each['Reservations'][0]['Id'],
                                        # 'order_line':product_p_line,
                                        'order_line': [(0, 0, {
                                            # 'name': self.env['product.product'].sudo().search([('name', '=', 'Dr0iver Expense')]).name,
                                            'name': self.env['product.product'].sudo().search(
                                                [('name', '=', 'Driver Expense')]).name,
                                            'product_id': self.env['product.product'].sudo().search(
                                                [('name', '=', 'Driver Expense')]).id,
                                            'product_qty': 1,
                                            'product_uom': self.env['uom.uom'].sudo().search([('name', '=', 'Units')]).id,
                                            'price_unit': price_unit,
                                            'basic_value': basic_value,
                                            'trip_cost': each['DriverRevenue'],
                                            # 'date_planned': time.strftime('%Y-%m-%d'),
                                            'date_planned': datetime.now().date().strftime(DEFAULT_SERVER_DATE_FORMAT),
                                        })],
                                    })
                                    po.sudo().button_confirm()

                                    j = self.env['account.payment.method'].sudo().search([('name', '=', 'Manual')])[0]
                                    journal = self.env['account.journal'].sudo().search(
                                        [('name', '=', 'Cash'), ('company_id', '=', 1)])

                                    if po.amount_total > 0:
                                        inb = po.sudo().automatic_bill_creation()
                                        # inb = po.invoice_ids
                                        if not po.invoice_ids:
                                            inb = self.env['account.move'].search([('purchase_id', '=', po.id)])
                                        else:
                                            inb = po.invoice_ids
                                        # inb.sudo().action_invoice_open()
                                        # inb.sudo().action_invoice_open()
                                        # for line in po.invoice_ids.invoice_line_ids:
                                        #     line.basic_value = basic_value
                                        # line.trip_cost = each['DriverRevenue']
                                        if each['Reservations'][0]['PaymentType'] == True :
                                          if inb:
                                              if inb.state == 'draft':
                                                inb.action_post()
                                                # pmt_wizard = self.env['account.payment.register'].with_context(active_model='account.move',
                                                #                                                                active_ids=inb.ids).create({
                                                #     'payment_date': inb.date,
                                                #     'journal_id': self.env['account.journal'].search(
                                                #         [('name', '=', 'Cash'), ('company_id', '=', 1)]).id,
                                                #     'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                                                #     'amount': inb.amount_total,
                                                #
                                                # })
                                                # pmt_wizard._create_payments()





                                        # payment = self.env['account.payment'].sudo().create(
                                        #     {'partner_id': driver_id.id,
                                        #      'amount': po.amount_total,
                                        #      'payment_type': 'outbound',
                                        #      'payment_method_id': self.env.ref(
                                        #          'account.account_payment_method_manual_in').id,
                                        #      'journal_id': journal.id,
                                        #      'partner_type': 'supplier',
                                        #      # 'currency_id': self.currency_usd_id,
                                        #      'ref': po.name+'=>'+driver_id.name,
                                        #      # 'move_id': inb.id
                                        #
                                        #      })
                                        #
                                        # m = payment.sudo().action_post()
                                        # inb.action_post()

                            order = self.env['sale.order']
                            if each['Reservations']:
                                if not self.env['sale.order'].sudo().search(
                                        [('trip_id', '=', each['Reservations'][0]['TripId'])]):
                                    partner_id = self.env['res.partner'].sudo().search(
                                        [('passenger_id', '=', each['Reservations'][0]['PassengerId'])])
                                    if not partner_id:
                                        partner_id = self.env['res.partner'].sudo().create({
                                            'name': each['Reservations'][0]['PassengerName'],
                                            'passenger_id': each['Reservations'][0]['PassengerId'],
                                            'mobile': each['Reservations'][0]['PassengerPhoneNumber'],
                                            'email': each['Reservations'][0]['PassengerEmail'],
                                            'type_of_customer': 'b_c',
                                            'schema_id': 'IQA',
                                            'schema_id_no': 'xxxx'

                                        })
                                    tax_ids = self.env['account.tax'].search(
                                        [('name', '=', 'VAT 15%'), ('type_tax_use', '=', 'sale')])
                                    # tax_ids += self.env['account.tax'].search(
                                    #     [('name', '=', 'Percentage 7%'), ('type_tax_use', '=', 'sale')])
                                    excluded_value = 0
                                    actual = 0
                                    # each['Distance']
                                    # each['KMPrice']
                                    # each['CaptainPounce']
                                    # each['TransportAuthorityFee']
                                    # each['AirportAdditionalFees']
                                    # each['MinimumPay']
                                    # each['CouponValue']
                                    distance_amount = each['Distance'] * each['KMPrice']
                                    actual = distance_amount + each['CaptainPounce'] + each['TransportAuthorityFee'] + each[
                                        'AirportAdditionalFees'] + each['MinimumPay']
                                    tax_value_system = actual * 7 / 100
                                    applicable_for = tax_value_system + actual - each['CouponValue']

                                    basic_value = 0
                                    price_unit = 0
                                    if tax_ids:
                                        tax = 0
                                        for eachs in tax_ids:
                                            if eachs.children_tax_ids:
                                                for ch in eachs.children_tax_ids:
                                                    tax += ch.amount
                                            else:
                                                tax += eachs.amount
                                        value = tax
                                        # basic_value = each['TripCost'] * value / 100
                                        # basic_value = each['TripCost'] * 100 / value
                                        # basic_value1 = each['TripCost'] - basic_value
                                        # line.basic_value = basic_value
                                        # line.basic_value = basic_value

                                        # line.total_amount = line.quantity * line.amount

                                        # value = tax
                                        # basic_value = applicable_for * value / 100
                                        price_unit = applicable_for

                                        # excluded_value = 1 * basic_value1

                                    product_line = []
                                    line = (0, 0, {
                                        'product_id': self.env['product.product'].sudo().search(
                                            [('name', '=', 'Rehla Car')]).id,
                                        'product_uom_qty': each['Reservations'][0]['SeatCount'],
                                        # 'price_unit': each['Reservations'][0]['SeatsCost'],
                                        # 'price_unit': each['TripCost'],
                                        'basic_value': basic_value,
                                        'trip_cost': each['TripCost'],
                                        # 'price_unit': excluded_value,
                                        'price_unit': price_unit,
                                        'name': self.env['product.product'].sudo().search([('name', '=', 'Rehla Car')]).name,
                                        'tax_id': [(6, 0, tax_ids.ids)],
                                        'product_uom': (self.env['uom.uom'].sudo().search([('name', '=', 'Units')])).id,

                                    })
                                    product_line.append(line)
                                    # import datetime
                                    date = each['CreationDate'].split('T')[0]
                                    # aDateTime = datetime.datetime.fromisoformat('2020-10-04 22:47:00')
                                    invoice_date = each['CreationDate'].split('T')[0].split('-')
                                    month = invoice_date[1]
                                    day = invoice_date[2]
                                    year = invoice_date[0]
                                    vals = {
                                        'partner_id': partner_id.id,
                                        'car_categ': str(each['CarCategoryId']),
                                        'trip_id': each['Reservations'][0]['TripId'],
                                        'rehla_id': each['Reservations'][0]['Id'],
                                        'payment_type': str(each['Reservations'][0]['PaymentType']),
                                        'govt_char': each['TransportAuthorityFee'],
                                        'additional_airport': each['AirportAdditionalFees'],
                                        'status_of_trip': str(each['Reservations'][0]['StatusId']),
                                        'order_line': product_line,
                                        'mobile': each['Reservations'][0]['PassengerPhoneNumber'],
                                        'distance': each['Distance'],
                                        'per_km': each['KMPrice'],
                                        'bonus': each['CaptainPounce'],
                                        'transportation_aut': each['TransportAuthorityFee'],
                                        'airport_additional': each['AirportAdditionalFees'],
                                        'taxvalue_system': tax_value_system,
                                        'coupon_value': each['CouponValue'],
                                        'creation_date':year + '-' + month + '-' + day,
                                        'basic_fire': each['MinimumPay'],
                                    }
                                    order = self.env['sale.order'].sudo().create(vals)
                                    order.sudo().action_confirm()
                                    if order.status_of_trip != '4':
                                        # invoice = order.action_invoice_create()
                                        invoice = order._create_invoices()
                                        # inb = self.env['account.move'].sudo().browse(invoice[0])
                                        inb1 = invoice
                                        # inb.sudo().action_invoice_open()
                                        # inb.sudo().action_invoice_open()
                                        for line in inb1.invoice_line_ids:
                                            line.basic_value = basic_value
                                            line.trip_cost = each['TripCost']
                                        # inb.sudo().action_post()
                                        # journal = self.env['account.journal'].sudo().search(
                                        #     [('name', '=', 'Cash'), ('company_id', '=', 1)])
                                        #
                                        # payment = self.env['account.payment'].sudo().create(
                                        #     {'partner_id': order.partner_id.id,
                                        #      'amount': order.amount_total,
                                        #      'payment_type': 'inbound',
                                        #      'payment_method_id': self.env.ref(
                                        #          'account.account_payment_method_manual_in').id,
                                        #      'journal_id': journal.id,
                                        #      'partner_type': 'customer',
                                        #      # 'currency_id': self.currency_usd_id,
                                        #      'ref': order.name + '=>' + order.partner_id.name,
                                        #      # 'move_id': inb.id
                                        #
                                        #      })
                                        # payment.sudo().action_post()

                                        if inb1:
                                            if inb1.state == 'draft':
                                                inb1.action_post()
                                                # pmt_wizard = self.env['account.payment.register'].with_context(
                                                #     active_model='account.move',
                                                #     active_ids=inb1.ids).create({
                                                #     'payment_date': inb1.date,
                                                #     'journal_id': self.env['account.journal'].search(
                                                #         [('name', '=', 'Cash'), ('company_id', '=', 1)]).id,
                                                #     'payment_method_id': self.env.ref(
                                                #         'account.account_payment_method_manual_in').id,
                                                #     'amount': inb1.amount_total,
                                                #
                                                # })
                                                # pmt_wizard._create_payments()

                                        if order:
                                            driv = each['DriverRevenue'] + each['VATValue']
                                            self.env['profit.car.orders'].sudo().create({
                                                'date': datetime.today().date(),
                                                'passenger_id': order.partner_id.passenger_id,
                                                'trip_id': each['Reservations'][0]['TripId'],
                                                'rehla_id': each['Reservations'][0]['Id'],
                                                'reh_driver_id': driver_id.reh_driver_id,
                                                'driver_cost': each['DriverRevenue'],
                                                'trip_cost': each['TripCost'],
                                                'tax_amount': each['VATValue'],
                                                'profit': each['TripCost'] - driv,
                                                'passenger': order.partner_id.id,
                                                'driver': driver_id.id,
                                                'revenue_profit': each['TaxValueAndSystemRevenue']
                                            })
                                            percentage = 0
                                            wallet_amount = 0
                                            if each['Reservations'][0]['PaymentType'] == True:
                                                percentage = each['TripCost'] * 22 / 100
                                                wallet_amount = each['TripCost'] - percentage
                                            if each['Reservations'][0]['PaymentType'] == False:
                                                # percentage = each['TripCost'] * 22 / 100
                                                wallet_amount = each['TripCost']

                                            self.env['wallet.amount'].sudo().create({
                                                'date': datetime.today().date(),
                                                'passenger_id': order.partner_id.id,
                                                'trip_id': each['Reservations'][0]['TripId'],
                                                'rehla_id': each['Reservations'][0]['Id'],
                                                'reh_driver_id': driver_id.reh_driver_id,
                                                'driver_cost': each['DriverRevenue'],
                                                'trip_cost': each['TripCost'],
                                                'driver_id': driver_id.id,
                                                'passenger': order.partner_id.id,
                                                'payment_type': str(each['Reservations'][0]['PaymentType']),
                                                'wallet_amount': wallet_amount
                                            })
                                            vals = {
                                                'journal_id': self.env['account.journal'].search(
                                                    [('name', '=', 'Miscellaneous Operations'),
                                                     ('company_id', '=', 1)]).id,
                                                'state': 'draft',
                                                'ref': driver_id.name
                                            }
                                            pay_id_list = []
                                            move_id = self.env['account.move'].create(vals)
                                            partner_id = driver_id.id
                                            label = driver_id.name

                                            # if self.type_of_credit == False:
                                            temp = (0, 0, {
                                                'account_id': self.env['account.account'].sudo().search(
                                                    [('name', '=', 'Product Sales'),
                                                     ('company_id', '=', 1)]).id,
                                                'name': label,
                                                'move_id': move_id.id,
                                                'date': datetime.today().date(),
                                                'partner_id': driver_id.id,
                                                'debit': wallet_amount,
                                                'credit': 0,
                                            })
                                            pay_id_list.append(temp)

                                            acc = self.env['account.account'].sudo().search(
                                                [('name', '=', 'Account Receivable'),
                                                 ('company_id', '=', 1)])
                                            temp = (0, 0, {
                                                'account_id': acc.id,
                                                'name': label,
                                                'move_id': move_id.id,
                                                'date': datetime.today().date(),
                                                'partner_id': driver_id.id,
                                                'debit': 0,
                                                'credit': wallet_amount,
                                            })
                                            pay_id_list.append(temp)
                                            move_id.line_ids = pay_id_list
                                            # if move_id.state == 'draft':
                                            #    move_id.sudo().action_post()


                                    else:
                                        order.sudo().action_cancel()

