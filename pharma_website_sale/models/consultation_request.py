# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


class PharmacyConsultationRequest(models.Model):
    _name = 'pharmacy.consultation.request'
    _description = 'Yêu cầu tư vấn thuốc'

    product_id = fields.Many2one(
        'product.template',
        string='Thuốc cần tư vấn',
        readonly=True
    )

    pharma_product_type = fields.Selection(
        related='product_id.pharma_product_type',
        string='Phân loại dược phẩm',
        readonly=True,
        store=True
    )

    customer_name = fields.Char(
        string='Họ và tên',
        required=True
    )

    phone = fields.Char(
        string='Số điện thoại',
        required=True
    )

    email = fields.Char(
        string='Email'
    )

    note = fields.Text(
        string='Nội dung cần tư vấn'
    )

    state = fields.Selection([
        ('new', 'Mới'),
        ('contacted', 'Đã liên hệ'),
        ('done', 'Hoàn tất'),
    ], string='Trạng thái', default='new')

    @api.constrains('phone')
    def _check_phone(self):
        for record in self:
            if record.phone:
                if not record.phone.isdigit():
                    raise ValidationError('Số điện thoại chỉ được chứa chữ số.')

                if len(record.phone) != 10:
                    raise ValidationError('Số điện thoại phải gồm đúng 10 số.')

    @api.constrains('email')
    def _check_email(self):
        for record in self:
            if record.email:
                pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

                if not re.match(pattern, record.email):
                    raise ValidationError('Email không đúng định dạng.')

    def action_mark_contacted(self):
        for record in self:
            record.state = 'contacted'

    def action_mark_done(self):
        for record in self:
            record.state = 'done'