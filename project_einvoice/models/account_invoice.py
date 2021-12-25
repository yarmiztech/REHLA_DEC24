from odoo import models,fields,api
from datetime import datetime


from uuid import uuid4
import qrcode
import base64
import logging

from lxml import etree

class AccountInvoice(models.Model):
    # _inherit = 'account.invoice'
    _inherit = 'account.move'


    def default_bank_details(self):
        bank_details = self.env.company.partner_id.bank_ids
        if bank_details:
            return bank_details[0].id
        else:
            return None

    # datetime_field = fields.Datetime(string="Create Date",default=lambda self: fields.Datetime.now())
    # decoded_data = fields.Char('Decoded Data')
    company_bank_id = fields.Many2one('res.partner.bank',default=default_bank_details)


    def print_einvoice(self):
        return self.env.ref('project_einvoice.ratal_invoice_report').report_action(self)

    def total_amount_to_words(self):
        self.check_amount_in_words = self.currency_id.amount_to_text(self.amount_total)
        return self.check_amount_in_words

    def _ubl_add_attachments(self, parent_node, ns, version="2.1"):
        self.ensure_one()
        self.billing_refence(parent_node, ns, version="2.1")
        # if self.decoded_data:
        self.testing()
        self.qr_code(parent_node, ns, version="2.1")
        self.qr_1code(parent_node, ns, version="2.1")
        self.pih_code(parent_node, ns, version="2.1")

        # self.signature_refence(parent_node, ns, version="2.1")
        # if self.company_id.embed_pdf_in_ubl_xml_invoice and not self.env.context.get(
        #     "no_embedded_pdf"
        # ):
        # self.signature_refence(parent_node, ns, version="2.1")
        filename = "Invoice-" + self.name + ".pdf"
        docu_reference = etree.SubElement(
            parent_node, ns["cac"] + "AdditionalDocumentReference"
        )
        docu_reference_id = etree.SubElement(docu_reference, ns["cbc"] + "ID")
        docu_reference_id.text = filename
        attach_node = etree.SubElement(docu_reference, ns["cac"] + "Attachment")
        binary_node = etree.SubElement(
            attach_node,
            ns["cbc"] + "EmbeddedDocumentBinaryObject",
            mimeCode="application/pdf",
            filename=filename,
        )
        ctx = dict()
        ctx["no_embedded_ubl_xml"] = True
        ctx["force_report_rendering"] = True
        # pdf_inv = (
        #     self.with_context(ctx)
        #     .env.ref("account.account_invoices")
        #     ._render_qweb_pdf(self.ids)[0]
        # )
        ########changed########################
        pdf_inv = self.with_context(ctx).env.ref(
            'account_invoice_ubl.account_invoices_1')._render_qweb_pdf(self.ids)[0]
        pdf_inv = self.with_context(ctx).env.ref(
            'account_invoice_ubl.account_invoices_b2b')._render_qweb_pdf(self.ids)[0]
        pdf_inv = self.with_context(ctx).env.ref(
            'account_invoice_ubl.account_invoices_b2b_credit')._render_qweb_pdf(self.ids)[0]
        # pdf_inv = self.with_context(ctx).env.ref(
        #     'account_invoice_ubl.account_invoices_b2b_debit')._render_qweb_pdf(self.ids)[0]
        pdf_inv = self.with_context(ctx).env.ref(
            'account_invoice_ubl.account_invoices_b2c')._render_qweb_pdf(self.ids)[0]
        pdf_inv = self.with_context(ctx).env.ref(
            'account_invoice_ubl.account_invoices_b2c_credit')._render_qweb_pdf(self.ids)[0]
        # +++++++++++++++++++++++++++++++OUR CUSTOMES ADD HERE+++++++++++++++++++++++++++++++++++++
        pdf_inv = self.with_context(ctx).env.ref(
            'project_einvoice.ratal_invoice_report')._render_qweb_pdf(self.ids)[0]
        pdf_inv = self.with_context(ctx).env.ref(
            'project_einvoice.accs_invoice_report')._render_qweb_pdf(self.ids)[0]
        # -----------------------------aboveeeeeeee---------------------------------

        binary_node.text = base64.b64encode(pdf_inv)
        # self.qr3_code(parent_node, ns, version="2.1")

        # filename = "ICV"
        # icv_reference = etree.SubElement(
        #     parent_node, ns["cac"] + "AdditionalDocumentReference"
        # )
        # icv_reference_id = etree.SubElement(icv_reference, ns["cbc"] + "ID")
        # icv_reference_id.text = filename
        # icv_reference_node = etree.SubElement(icv_reference, ns["cac"] + "UUID")
        # icv_reference_node.text = self.name

    @api.model
    def _get_invoice_report_names(self):
        return [
            "account.report_invoice",
            "account.report_invoice_with_payments",
            "account_invoice_ubl.report_invoice_1",
            "account_invoice_ubl.report_invoice_b2b",
            "account_invoice_ubl.report_invoice_b2b_credit",
            # "account_invoice_ubl.report_invoice_b2b_debit",
            "account_invoice_ubl.report_invoice_b2c",
            "account_invoice_ubl.report_invoice_b2c_credit",
            # "account_invoice_ubl.report_invoice_b2c_debit",
            "project_einvoice.ratal_invoice_report_view_1",
            "project_einvoice.accs_invoice_report_view_1",

        ]

class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"


    @classmethod
    def _get_invoice_reports_ubl(cls):
        return [
            "account.report_invoice",
            'account_invoice_ubl.report_invoice_1',
            'account_invoice_ubl.report_invoice_b2b',
            'account_invoice_ubl.report_invoice_b2b_credit',
            'account_invoice_ubl.report_invoice_b2b_debit',
            'account_invoice_ubl.report_invoice_b2c',
            'account_invoice_ubl.report_invoice_b2c_credit',
            'account_invoice_ubl.report_invoice_b2c_debit',
            "account.report_invoice_with_payments",
            "account.account_invoice_report_duplicate_main",
            "project_einvoice.ratal_invoice_report_view_1",
            "project_einvoice.accs_invoice_report_view_1",

        ]



class AccountInvoiceLine(models.Model):
    # _inherit = 'account.invoice.line'
    _inherit = 'account.move.line'


    def total_amount(self):
        total = 0.00
        total_amount = 0.00
        for vat in self:

            total = vat.price_subtotal * 0.15
            total_amount =total + vat.price_subtotal
        return total_amount


    def product_arabic(self):
        for products in self:
            product = products.product_id.name
            product_template = self.env['product.template'].search([('name','=',product)])
            for ar in product_template:
                return ar.arabic





