# -*- coding: utf-8 -*-
import re
from odoo import fields, models
from odoo.exceptions import ValidationError


def validate_phone_number(phone):
    if not phone:
        return False
    clean_phone = phone.replace(' ', '').replace('\t', '').replace('-', '')
    return bool(re.match(r'^\+?[0-9]{9,15}$', clean_phone))


class PharmacyPrescriptionCustomerWizard(models.TransientModel):
    _name = 'pharmacy.prescription.customer.wizard'
    _description = 'Tạo khách hàng cho đơn thuốc kê đơn'

    prescription_id = fields.Many2one('pharmacy.prescription', string='Đơn thuốc kê đơn', required=True, readonly=True)
    name = fields.Char(string='Họ và tên', required=True)
    phone = fields.Char(string='Số điện thoại', required=True)
    email = fields.Char(string='Email')
    street = fields.Char(string='Địa chỉ')

    def action_create_customer_and_confirm(self):
        self.ensure_one()
        phone = self.phone.replace(' ', '').replace('\t', '').replace('-', '')
        if not validate_phone_number(phone):
            raise ValidationError('Số điện thoại không hợp lệ. Vui lòng nhập đúng định dạng, ví dụ 0912345678 hoặc +84912345678.')
        partner = self.env['res.partner'].create({
            'name': self.name,
            'phone': phone,
            'email': self.email,
            'street': self.street,
            'customer_rank': 1,
        })
        return self.prescription_id._create_sale_order(partner)
