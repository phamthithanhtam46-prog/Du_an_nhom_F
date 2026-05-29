# -*- coding: utf-8 -*-
import re
from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError


def validate_phone_number(phone):
    if not phone:
        return False
    clean_phone = phone.replace(' ', '').replace('\t', '').replace('-', '')
    return bool(re.match(r'^\+?[0-9]{9,15}$', clean_phone))


class PharmacyPrescription(models.Model):
    _name = 'pharmacy.prescription'
    _description = 'Đơn thuốc kê đơn'
    _order = 'id desc'

    name = fields.Char(string='Mã đơn thuốc', default='New', readonly=True, copy=False)
    customer_name = fields.Char(string='Họ và tên', required=True)
    phone = fields.Char(string='Số điện thoại', required=True)
    birth_date = fields.Date(string='Ngày sinh')
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác'),
    ], string='Giới tính')
    weight = fields.Float(string='Cân nặng')
    prescription_date = fields.Date(string='Ngày kê đơn')
    note = fields.Text(string='Ghi chú yêu cầu tư vấn')

    prescription_image = fields.Binary(string='Hình ảnh đơn thuốc', attachment=True, required=True)
    prescription_image_filename = fields.Char(string='Tên file ảnh')

    doctor_name = fields.Char(string='Bác sĩ kê đơn')
    doctor_license = fields.Char(string='Số chứng chỉ hành nghề')
    medical_facility = fields.Char(string='Cơ sở khám chữa bệnh')

    guardian_name = fields.Char(string='Người giám hộ')
    guardian_document = fields.Char(string='CCCD người giám hộ')
    is_child = fields.Boolean(string='Trẻ em dưới 72 tháng', compute='_compute_is_child', store=True)

    has_pregnancy = fields.Boolean(string='Mang thai / cho con bú')
    has_kidney_disease = fields.Boolean(string='Bệnh gan/thận')
    has_hypertension = fields.Boolean(string='Cao huyết áp')
    other_conditions = fields.Text(string='Bệnh nền khác')

    line_ids = fields.One2many('pharmacy.prescription.line', 'prescription_id', string='Danh sách thuốc')

    partner_id = fields.Many2one('res.partner', string='Khách hàng Odoo', readonly=True)
    pharmacist_id = fields.Many2one('res.users', string='Dược sĩ duyệt', readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='Đơn bán hàng', readonly=True)

    state = fields.Selection([
        ('draft', 'Chờ xử lý'),
        ('rejected', 'Từ chối'),
        ('confirmed', 'Đã tạo đơn bán'),
    ], string='Trạng thái', default='draft', readonly=True)

    @api.depends('birth_date', 'prescription_date')
    def _compute_is_child(self):
        for rec in self:
            rec.is_child = False
            if rec.birth_date:
                date_to_compare = rec.prescription_date or fields.Date.today()
                months = (date_to_compare.year - rec.birth_date.year) * 12 + date_to_compare.month - rec.birth_date.month
                if date_to_compare.day < rec.birth_date.day:
                    months -= 1
                rec.is_child = months < 72

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('pharmacy.prescription') or 'RX00001'
        return super().create(vals_list)

    @api.constrains('phone')
    def _check_phone(self):
        for rec in self:
            if rec.phone and not validate_phone_number(rec.phone):
                raise ValidationError('Số điện thoại không hợp lệ. Vui lòng nhập đúng định dạng, ví dụ 0912345678 hoặc +84912345678.')

    def write(self, vals):
        for rec in self:
            if rec.state == 'confirmed' and set(vals) - {'partner_id', 'pharmacist_id', 'sale_order_id', 'state'}:
                raise ValidationError('Không thể chỉnh sửa đơn thuốc đã tạo đơn bán.')
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state == 'confirmed':
                raise ValidationError('Không thể xóa đơn thuốc đã tạo đơn bán.')
        return super().unlink()

    def action_reject(self):
        self.ensure_one()
        if not self.env.user.has_group('module_6.group_pharmacy_pharmacist'):
            raise ValidationError('Chỉ Dược sĩ mới có quyền từ chối đơn thuốc.')
        if self.state == 'confirmed':
            raise ValidationError('Đơn thuốc đã tạo đơn bán, không thể từ chối.')
        self.write({'state': 'rejected', 'pharmacist_id': self.env.user.id})

    def _validate_prescription(self):
        self.ensure_one()
        if self.sale_order_id:
            raise ValidationError('Đơn thuốc này đã được tạo đơn bán hàng.')
        if not self.prescription_image:
            raise ValidationError('Vui lòng upload hình ảnh đơn thuốc.')
        if not self.customer_name:
            raise ValidationError('Vui lòng nhập họ và tên khách hàng.')
        if not self.phone:
            raise ValidationError('Vui lòng nhập số điện thoại.')
        if self.prescription_date and fields.Date.today() - self.prescription_date > timedelta(days=5):
            raise ValidationError('Đơn thuốc đã quá hạn hiệu lực, chỉ chấp nhận trong vòng 5 ngày kể từ ngày kê đơn.')
        if self.is_child:
            if not self.guardian_name:
                raise ValidationError('Bệnh nhi dưới 72 tháng tuổi bắt buộc nhập họ tên người giám hộ.')
            if not self.guardian_document:
                raise ValidationError('Bệnh nhi dưới 72 tháng tuổi bắt buộc nhập CCCD người giám hộ.')
        if not self.line_ids:
            raise ValidationError('Vui lòng thêm ít nhất một dòng thuốc.')
        for line in self.line_ids:
            product = line.product_id
            if not product:
                raise ValidationError('Vui lòng chọn sản phẩm trong dòng thuốc.')
            if line.quantity <= 0:
                raise ValidationError('Số lượng thuốc phải lớn hơn 0.')
            if product.product_tmpl_id.pharma_product_type != 'rx':
                raise ValidationError('Sản phẩm "%s" không phải thuốc kê đơn.' % product.display_name)
            if self.has_pregnancy and product.product_tmpl_id.contraindicated_pregnancy:
                raise ValidationError('Thuốc "%s" chống chỉ định với phụ nữ có thai/cho con bú.' % product.display_name)
            if self.has_kidney_disease and product.product_tmpl_id.contraindicated_kidney:
                raise ValidationError('Thuốc "%s" chống chỉ định với bệnh nhân suy gan/thận.' % product.display_name)
            if self.has_hypertension and product.product_tmpl_id.contraindicated_hypertension:
                raise ValidationError('Thuốc "%s" chống chỉ định với bệnh nhân cao huyết áp.' % product.display_name)

    def action_confirm(self):
        self.ensure_one()
        if not self.env.user.has_group('module_6.group_pharmacy_pharmacist'):
            raise ValidationError('Chỉ Dược sĩ mới có quyền duyệt đơn thuốc.')
        self._validate_prescription()
        phone = self.phone.replace(' ', '').replace('\t', '').replace('-', '')
        partner = self.env['res.partner'].search([('phone', '=', phone)], limit=1)
        if partner:
            return self._create_sale_order(partner)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tạo khách hàng',
            'res_model': 'pharmacy.prescription.customer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_prescription_id': self.id,
                'default_name': self.customer_name,
                'default_phone': phone,
            },
        }

    def _create_sale_order(self, partner):
        self.ensure_one()
        order_lines = []
        for line in self.line_ids:
            description = line.product_id.display_name
            if line.original_medicine_name:
                description += '\nThuốc gốc trên đơn: %s' % line.original_medicine_name
            if line.dosage:
                description += '\nLiều lượng: %s' % line.dosage
            order_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_id.uom_id.id,
                'name': description,
            }))
        note_parts = [
            'Thông tin đơn thuốc kê đơn:',
            '- Khách hàng: %s' % self.customer_name,
            '- Số điện thoại: %s' % self.phone,
            '- Ngày kê đơn: %s' % (self.prescription_date or ''),
        ]
        if self.doctor_name:
            note_parts.append('- Bác sĩ kê đơn: %s' % self.doctor_name)
        if self.medical_facility:
            note_parts.append('- Cơ sở y tế: %s' % self.medical_facility)
        if self.note:
            note_parts.append('- Ghi chú: %s' % self.note)
        sale_order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'origin': self.name,
            'note': '\n'.join(note_parts),
            'order_line': order_lines,
        })
        self.write({
            'partner_id': partner.id,
            'pharmacist_id': self.env.user.id,
            'sale_order_id': sale_order.id,
            'state': 'confirmed',
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Đơn bán hàng',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }


class PharmacyPrescriptionLine(models.Model):
    _name = 'pharmacy.prescription.line'
    _description = 'Dòng thuốc kê đơn'
    _order = 'id asc'

    prescription_id = fields.Many2one('pharmacy.prescription', string='Đơn thuốc kê đơn', required=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product',
        string='Sản phẩm',
        required=True,
        domain="[('product_tmpl_id.pharma_product_type', '=', 'rx')]"
    )
    product_code = fields.Char(string='Mã sản phẩm', related='product_id.default_code', readonly=True)
    medicine_name = fields.Char(string='Tên thuốc', related='product_id.display_name', readonly=True)
    drug_group_id = fields.Many2one('product.category', string='Nhóm thuốc', related='product_id.categ_id', readonly=True)
    quantity = fields.Float(string='Số lượng', default=1.0, required=True)
    uom_id = fields.Many2one('uom.uom', string='ĐVT', related='product_id.uom_id', readonly=True)
    original_medicine_name = fields.Char(string='Tên thuốc gốc trên đơn')
    dosage = fields.Char(string='Liều lượng')
