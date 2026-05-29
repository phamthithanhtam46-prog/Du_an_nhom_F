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

    picking_id      = fields.Many2one('stock.picking', string='Phiếu xuất kho')
    sale_order_id   = fields.Many2one('sale.order', string='Sale Order')
    sale_order_name = fields.Char(related='sale_order_id.name', readonly=True, store=False)

    # ── Shared ──
    product_name = fields.Char(string='Sản phẩm', readonly=True)

    # ── Expired fields ──
    lot_name        = fields.Char(string='Lot',  readonly=True)
    expiry_date     = fields.Char(string='HSD',  readonly=True)   # lưu dạng dd/mm/yyyy

    # ── Insufficient fields ──
    qty_demand      = fields.Char(string='Yêu cầu', readonly=True)
    qty_available   = fields.Char(string='Tồn kho', readonly=True)
    qty_shortage    = fields.Char(string='Thiếu',   readonly=True)

    # ── Legacy (giữ lại để không break nếu có chỗ nào còn dùng) ──
    title   = fields.Char(string='Tiêu đề',    readonly=True)
    message = fields.Char(string='Chi tiết lỗi', readonly=True)

    # ──────────────────────────────────────────────────────────────
    def action_replace_products(self):
        """Set qty = 0 cho sản phẩm lỗi rồi mở Sale Order."""
        self.ensure_one()
        so      = self.sale_order_id
        picking = self.picking_id

        if not so:
            raise UserError(_('Không tìm thấy đơn bán hàng liên kết.'))

        if so.state == 'sale' and so.locked:
            so.action_unlock()

        now = fields.Datetime.now()
        problem_product_ids = set()

        for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
            product   = move.product_id
            has_problem = False

            if product.tracking and product.tracking != 'none':
                for ml in move.move_line_ids:
                    if ml.lot_id and ml.lot_id.expiration_date and ml.lot_id.expiration_date < now:
                        has_problem = True

            qty_avail = product.with_context(location=picking.location_id.id).qty_available
            if qty_avail < move.product_uom_qty:
                has_problem = True

            if has_problem:
                problem_product_ids.add(product.id)

        for line in so.order_line.filtered(lambda l: l.product_id.id in problem_product_ids):
            line.product_uom_qty = 0

        return {
            'type': 'ir.actions.act_window',
            'name': f'{so.name} — Thêm sản phẩm thay thế',
            'res_model': 'sale.order',
            'res_id': so.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_validate_anyway(self):
        """Vẫn xác nhận — chỉ dùng khi thiếu số lượng."""
        self.ensure_one()
        if not self.picking_id:
            return {'type': 'ir.actions.act_window_close'}
        return self.picking_id.with_context(skip_minhchau_check=True).button_validate()