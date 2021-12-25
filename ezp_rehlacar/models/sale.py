# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import date
from datetime import datetime
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    rehla_id = fields.Integer('Rehla Id')
    trip_id = fields.Integer('Trip Id')
    govt_char = fields.Float('TransportAuthorityFee')
    additional_airport = fields.Float('AirportAdditionalFees')
    creation_date = fields.Date(string="Creation Date")
    status_of_trip = fields.Selection([
        ('1', 'Pending'),
        ('2', 'Accepted'),
        ('3', 'Rejected'),
        ('4', 'Canceled'),
        ('5', 'Finished'),
        ('6', 'RatedByPassenger'),
    ], string='Trip Status', readonly=True, copy=False, index=True, track_visibility='onchange',
        track_sequence=3,
    )
    car_categ  = fields.Selection([
        ('1', 'Go'),
        ('2', 'Taxi'),
        ('3', 'VIP'),
        ('4', 'Family'),
        ('5', 'Ladies'),
        ('6', 'Go Plus'),
        ('7', 'Family Plus'),
    ], string='Car Category', readonly=True, copy=False, index=True, track_visibility='onchange',
        track_sequence=3,
    )
    payment_type = fields.Selection([
        ('True', 'cash'),
        ('False', 'Wallet'),

    ], string='PaymentType', readonly=True, copy=False, index=True, track_visibility='onchange',
        track_sequence=3,
    )

    basic_fire = fields.Float(string='Basic Fire')
    bonus = fields.Float(string='Bonus')
    transportation_aut = fields.Float(string='Transportation Auth')
    airport_additional = fields.Float(string='Airport Additional')
    distance = fields.Float(string='Distance')
    per_km = fields.Float(string='Km/Charge')
    taxvalue_system = fields.Float(string='TaxValue&SystemRevenue')
    coupon_value = fields.Float(string='CouponValue')
    mobile = fields.Char(string='Mobile')
    rehla_uniq_id = fields.Integer(string='Rehla Unique Id')





    @api.constrains('partner_id')
    def onchange_partner(self):
        if self.partner_id:
            self.mobile = self.partner_id.mobile
            self.rehla_uniq_id = self.partner_id.reh_driver_id

    #
    #
    # @api.depends('order_line.price_total')
    # def _amount_all(self):
    #     """
    #     Compute the total amounts of the SO.
    #     """
    #     for order in self:
    #         amount_untaxed = amount_tax = 0.0
    #         for line in order.order_line:
    #             amount_untaxed += line.price_subtotal
    #             amount_tax += line.price_tax
    #     for l in self.order_line:
    #         if l.basic_value:
    #             amount_tax = l.basic_value
    #         order.update({
    #             'amount_untaxed': amount_untaxed,
    #             'amount_tax': amount_tax,
    #             'amount_total': amount_untaxed + amount_tax,
    #         })



class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    basic_value = fields.Float('Basic')
    trip_cost = fields.Float('Trip Cost')



class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    rehla_id = fields.Integer('Rehla Id')
    trip_id = fields.Integer('Trip Id')
    basic_fire = fields.Float(string='Basic Fire')
    bonus = fields.Float(string='Bonus')
    transportation_aut = fields.Float(string='Transportation Auth')
    airport_additional = fields.Float(string='Airport Additional')
    taxvalue_system = fields.Float(string='TaxValue&SystemRevenue')
    value_added = fields.Float(string='Vat-added tax')
    application_fee = fields.Float(string='Application Fees')
    coupon_value = fields.Float(string='CouponValue')
    mobile = fields.Char(string='Mobile')
    rehla_uniq_id = fields.Integer(string='Rehla Unique Id')
    reh_driver_id = fields.Integer('Driver Id')




    @api.constrains('partner_id')
    def onchange_partner(self):
        if self.partner_id:
            self.mobile = self.partner_id.mobile
            self.rehla_uniq_id = self.partner_id.reh_driver_id

    # @api.depends('partner_id')
    # def onchange_driver_partner(self):
    #     if self.partner_id:
    #         self.rehla_uniq_id = self.partner_id.reh_driver_id


    def automatic_bill_creation(self):
        # if self.picking_ids.state == 'done':

        create_bill = self.env.context.get('create_bill', False)
        account_id = self.env['account.account'].search(
            [('name', '=', 'Purchase Expense'), ('company_id', '=', self.env.user.company_id.id)])
        # override the context to get rid of the default filtering
        po = self
        list = []
        for po_line in self.order_line:
            new_line = (0,0,{
                'name': po_line.name,
                # 'origin': po.name,
                'account_id': account_id.id,
                'price_unit': po_line.price_unit,
                'purchase_line_id':po_line.id,
                'quantity': po_line.product_uom_qty,
                'discount': 0.0,
                'product_uom_id': po_line.product_id.uom_id.id,
                'product_id': po_line.product_id.id,
                # 'move_id': new_inv.id,
                'tax_ids': [(6, 0, po_line.taxes_id.ids)]
            })
            list.append(new_line)

            # po_line.invoice_lines = new_line




        new_inv = self.env['account.move'].create({
            'move_type': 'in_invoice',
            # 'invoiced_number':po.invoiced_number,
            'invoice_date':datetime.today().date(),
            # 'purchase_date':po.purchase_date,
            # 'vehicle_no':po.vehicle_no,
            'partner_id': po.partner_id.id,
            'purchase_id': po.id,
            'currency_id': po.currency_id.id,
            'company_id': po.company_id.id,
            'invoice_line_ids':list
            # 'origin': po.name,
            # 'tax_line_ids':po_line.taxes_id.ids
        })

        # for po_line in self.order_line:
        #     new_line = self.env['account.move.line'].create({
        #         'name': po_line.name,
        #         # 'origin': po.name,
        #         'account_id': account_id.id,
        #         'price_unit': po_line.price_unit,
        #         'quantity': po_line.product_uom_qty,
        #         'discount': 0.0,
        #         'product_uom_id': po_line.product_id.uom_id.id,
        #         'product_id': po_line.product_id.id,
        #         'move_id': new_inv.id,
        #         'tax_ids': [(6, 0, po_line.taxes_id.ids)]})
        #     po_line.invoice_lines = new_line
        # new_inv.compute_taxes()
        # new_inv.action_invoice_open()
        # new_inv.action_post()

    #
    # @api.depends('order_line.price_total')
    # def _amount_all(self):
    #     for order in self:
    #         amount_untaxed = amount_tax = 0.0
    #         for line in order.order_line:
    #             amount_untaxed += line.price_subtotal
    #             amount_tax += line.price_tax
    #             for line in self.order_line:
    #                 if line.basic_value:
    #                     amount_tax = line.basic_value
    #
    #         order.update({
    #             'amount_untaxed': order.currency_id.round(amount_untaxed),
    #             'amount_tax': order.currency_id.round(amount_tax),
    #             'amount_total': amount_untaxed + amount_tax,
    #         })


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"


    basic_value = fields.Float('Basic')
    trip_cost = fields.Float('Trip Cost')



class ResPartner(models.Model):
    _inherit = 'res.partner'

    passenger_id = fields.Integer('Passenger Id')
    reh_driver_id = fields.Integer('Driver Id')


class AccountMove(models.Model):
    _inherit = "account.move"

    #
    #
    # @api.one
    # @api.depends('invoice_line_ids.price_subtotal', 'invoice_line_ids.basic_value', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
    #              'currency_id', 'company_id', 'date_invoice', 'type', 'date')
    # def _compute_amount(self):
    #     round_curr = self.currency_id.round
    #     self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
    #     for line in self.invoice_line_ids:
    #         if line.basic_value:
    #             self.amount_tax = line.basic_value
    #         else:
    #             self.amount_tax = sum(round_curr(line.amount_total) for line in self.tax_line_ids)
    #     self.amount_total = self.amount_untaxed + self.amount_tax
    #     amount_total_company_signed = self.amount_total
    #     amount_untaxed_signed = self.amount_untaxed
    #     if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
    #         currency_id = self.currency_id
    #         rate_date = self._get_currency_rate_date() or fields.Date.today()
    #         amount_total_company_signed = currency_id._convert(self.amount_total, self.company_id.currency_id, self.company_id, rate_date)
    #         amount_untaxed_signed = currency_id._convert(self.amount_untaxed, self.company_id.currency_id, self.company_id, rate_date)
    #     sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
    #     self.amount_total_company_signed = amount_total_company_signed * sign
    #     self.amount_total_signed = self.amount_total * sign
    #     self.amount_untaxed_signed = amount_untaxed_signed * sign

    # @api.one
    # @api.depends(
    #     'state', 'currency_id', 'invoice_line_ids.price_subtotal','invoice_line_ids.basic_value',
    #     'move_id.line_ids.amount_residual',
    #     'move_id.line_ids.currency_id')
    # def _compute_residual(self):
    #     residual = 0.0
    #     residual_company_signed = 0.0
    #     sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
    #     for line in self._get_aml_for_amount_residual():
    #         residual_company_signed += line.amount_residual
    #         if line.currency_id == self.currency_id:
    #             residual += line.amount_residual_currency if line.currency_id else line.amount_residual
    #         else:
    #             if line.currency_id:
    #                 residual += line.currency_id._convert(line.amount_residual_currency, self.currency_id,
    #                                                       line.company_id, line.date or fields.Date.today())
    #             else:
    #                 residual += line.company_id.currency_id._convert(line.amount_residual, self.currency_id,
    #                                                                  line.company_id, line.date or fields.Date.today())
    #     self.residual_company_signed = abs(residual_company_signed) * sign
    #     self.residual_signed = abs(residual) * sign
    #     if self.company_id.id != 1:
    #         if self.amount_tcs:
    #             self.residual = abs(residual) + self.amount_tcs
    #         else:
    #             self.residual = abs(residual)
    #     else:
    #         self.residual = abs(residual)
    #     for line in self.invoice_line_ids:
    #         if line.basic_value:
    #             self.residual = self.amount_total
    #
    #     digits_rounding_precision = self.currency_id.rounding
    #     from odoo.tools import float_is_zero, pycompat
    #     if float_is_zero(self.residual, precision_rounding=digits_rounding_precision):
    #         self.reconciled = True
    #     else:
    #         self.reconciled = False


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    basic_value = fields.Float('Basic')
    trip_cost = fields.Float('Trip Cost')
