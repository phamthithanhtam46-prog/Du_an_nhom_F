# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MinhChauStockErrorWizard(models.TransientModel):
    _name = 'minhchau.stock.error.wizard'
    _description = 'Minh Chau Stock Error Wizard'

    error_type = fields.Selection([
        ('expired', 'Hết hạn sử dụng'),
        ('insufficient', 'Không đủ tồn kho'),
        ('both', 'Hết hạn & Không đủ tồn kho'),
    ], string='Loại lỗi', required=True)

    title = fields.Char(string='Tiêu đề', readonly=True)
    message = fields.Text(string='Chi tiết lỗi', readonly=True)
    picking_id = fields.Many2one('stock.picking', string='Phiếu xuất kho')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    sale_order_name = fields.Char(
        related='sale_order_id.name',
        readonly=True,
        store=False,
    )

    def action_go_to_sale_order(self):
        """Mở SO ở chế độ edit — Odoo không cho xóa dòng đã confirm,
           nên hướng dẫn user set qty=0 và thêm dòng mới."""
        if not self.sale_order_id:
            return {'type': 'ir.actions.act_window_close'}

        so = self.sale_order_id
        if so.state == 'sale' and so.locked:
            so.action_unlock()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'res_model': 'sale.order',
            'res_id': so.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'show_sale': True},
        }

    def action_replace_products(self):
        """
        Tự động xử lý các dòng lỗi trên SO:
        - Set qty = 0 cho dòng sản phẩm lỗi (hết hạn / thiếu hàng)
        - Mở SO để user thêm sản phẩm thay thế
        """
        self.ensure_one()
        so = self.sale_order_id
        picking = self.picking_id

        if not so:
            raise UserError(_('Không tìm thấy đơn bán hàng liên kết.'))

        # Unlock SO nếu đang locked
        if so.state == 'sale' and so.locked:
            so.action_unlock()

        now = fields.Datetime.now()
        problem_product_ids = set()

        # Thu thập các sản phẩm lỗi từ picking
        for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
            product = move.product_id
            has_problem = False

            # Kiểm tra hết hạn
            if product.tracking and product.tracking != 'none':
                if move.move_line_ids:
                    for ml in move.move_line_ids:
                        if ml.lot_id and ml.lot_id.expiration_date and ml.lot_id.expiration_date < now:
                            has_problem = True
                else:
                    quants = self.env['stock.quant'].search([
                        ('product_id', '=', product.id),
                        ('location_id', 'child_of', picking.location_id.id),
                        ('quantity', '>', 0),
                    ])
                    lots = quants.mapped('lot_id').filtered(lambda l: l)
                    if lots and all(l.expiration_date and l.expiration_date < now for l in lots):
                        has_problem = True

            # Kiểm tra thiếu số lượng
            qty_available = product.with_context(location=picking.location_id.id).qty_available
            if qty_available < move.product_uom_qty:
                has_problem = True

            if has_problem:
                problem_product_ids.add(product.id)

        # Set qty = 0 cho các dòng SO có sản phẩm lỗi
        for line in so.order_line.filtered(lambda l: l.product_id.id in problem_product_ids):
            line.product_uom_qty = 0

        # Mở SO để user thêm sản phẩm thay thế
        return {
            'type': 'ir.actions.act_window',
            'name': f'Chỉnh sửa {so.name} — Thêm sản phẩm thay thế',
            'res_model': 'sale.order',
            'res_id': so.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_validate_anyway(self):
        """Vẫn xác nhận - chỉ cho phép khi lỗi là thiếu số lượng."""
        self.ensure_one()
        if not self.picking_id:
            return {'type': 'ir.actions.act_window_close'}
        return self.picking_id.with_context(skip_minhchau_check=True).button_validate()

    def action_close(self):
        return {'type': 'ir.actions.act_window_close'}