# -*- coding: utf-8 -*-
from odoo import models, fields, _


class MinhChauStockPicking(models.Model):
    _inherit = 'stock.picking'

    def _check_immediate(self):
        normal = self.filtered(lambda p: p.picking_type_code != 'outgoing')
        if normal:
            return super(MinhChauStockPicking, normal)._check_immediate()
        return False

    def _pre_action_sanity_check(self):
        normal = self.filtered(lambda p: p.picking_type_code != 'outgoing')
        if normal:
            return super(MinhChauStockPicking, normal)._pre_action_sanity_check()
        return True

    def button_validate(self):
        if self.env.context.get('skip_minhchau_check'):
            return super().button_validate()

        for picking in self:
            if picking.picking_type_code != 'outgoing':
                continue

            now = fields.Datetime.now()

            # ── Dữ liệu hết hạn (lấy dòng đầu tiên) ──
            expired_info     = None   # dict: product_name, lot_name, expiry_date
            # ── Dữ liệu thiếu kho (lấy dòng đầu tiên) ──
            insufficient_info = None  # dict: product_name, qty_demand, qty_available, qty_shortage

            for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                product = move.product_id

                # ── Kiểm tra hết hạn ──
                if expired_info is None and product.tracking and product.tracking != 'none':
                    for ml in move.move_line_ids:
                        if ml.lot_id and ml.lot_id.expiration_date:
                            if ml.lot_id.expiration_date < now:
                                expired_info = {
                                    'product_name': product.name,
                                    'lot_name':     ml.lot_id.name,
                                    'expiry_date':  ml.lot_id.expiration_date.strftime('%d/%m/%Y'),
                                }
                                break
                    if expired_info is None and not move.move_line_ids:
                        quants = self.env['stock.quant'].search([
                            ('product_id',   '=', product.id),
                            ('location_id',  'child_of', picking.location_id.id),
                            ('quantity',     '>',  0),
                        ])
                        for q in quants:
                            if q.lot_id and q.lot_id.expiration_date and q.lot_id.expiration_date < now:
                                expired_info = {
                                    'product_name': product.name,
                                    'lot_name':     q.lot_id.name,
                                    'expiry_date':  q.lot_id.expiration_date.strftime('%d/%m/%Y'),
                                }
                                break

                # ── Kiểm tra thiếu tồn kho ──
                if insufficient_info is None:
                    qty_avail = product.with_context(location=picking.location_id.id).qty_available
                    if qty_avail < move.product_uom_qty:
                        shortage = move.product_uom_qty - qty_avail
                        insufficient_info = {
                            'product_name':  product.name,
                            'qty_demand':    f'{move.product_uom_qty:.1f}',
                            'qty_available': f'{qty_avail:.1f}',
                            'qty_shortage':  f'{shortage:.1f}',
                        }

            if not expired_info and not insufficient_info:
                continue

            # ── Xác định error_type ──
            if expired_info and insufficient_info:
                error_type = 'both'
            elif expired_info:
                error_type = 'expired'
            else:
                error_type = 'insufficient'

            sale_order = getattr(picking, 'sale_id', False)

            # ── Tạo wizard với các field tách biệt ──
            vals = {
                'error_type':  error_type,
                'picking_id':  picking.id,
                'sale_order_id': sale_order.id if sale_order else False,
            }

            if expired_info:
                vals.update({
                    'product_name': expired_info['product_name'],
                    'lot_name':     expired_info['lot_name'],
                    'expiry_date':  expired_info['expiry_date'],
                    # legacy
                    'title':   expired_info['product_name'],
                    'message': f"Lot: {expired_info['lot_name']} · HSD: {expired_info['expiry_date']}",
                })
            else:
                vals.update({
                    'product_name':  insufficient_info['product_name'],
                    'qty_demand':    insufficient_info['qty_demand'],
                    'qty_available': insufficient_info['qty_available'],
                    'qty_shortage':  insufficient_info['qty_shortage'],
                    # legacy
                    'title':   insufficient_info['product_name'],
                    'message': (
                        f"Yêu cầu: {insufficient_info['qty_demand']} · "
                        f"Tồn kho: {insufficient_info['qty_available']} · "
                        f"Thiếu: {insufficient_info['qty_shortage']}"
                    ),
                })

            wizard = self.env['minhchau.stock.error.wizard'].create(vals)

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'minhchau.stock.error.wizard',
                'res_id': wizard.id,
                'view_mode': 'form',
                'target': 'new',
                'name': 'Lỗi Xuất Kho',
            }

        return super().button_validate()