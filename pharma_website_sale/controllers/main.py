# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class PharmacyWebsiteSale(WebsiteSale):

    @http.route()
    def cart_update_json(self, product_id=None, line_id=None, add_qty=None, set_qty=None, **kw):
        if product_id:
            product = request.env['product.product'].sudo().browse(int(product_id))

            if product.exists() and product.product_tmpl_id.pharma_product_type == 'rx':
                return {
                    'error': 'Thuốc kê đơn cần được tư vấn trước khi mua.'
                }

        return super().cart_update_json(
            product_id=product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            **kw
        )
    
    @http.route('/pharmacy/consultation', type='http', auth='public', website=True)
    def pharmacy_consultation_form(self, product_id=None, **kw):
        product = None

        if product_id:
            product = request.env['product.template'].sudo().browse(int(product_id))

        return request.render('pharma_website_sale.pharmacy_consultation_form', {
            'product': product,
        })
    
    @http.route('/pharmacy/consultation/submit', type='http', auth='public', website=True, methods=['POST'])
    def pharmacy_consultation_submit(self, **post):
        product_id = post.get('product_id')

        request.env['pharmacy.consultation.request'].sudo().create({
            'product_id': int(product_id) if product_id else False,
            'customer_name': post.get('customer_name'),
            'phone': post.get('phone'),
            'email': post.get('email'),
            'note': post.get('note'),
        })

        return request.render('pharma_website_sale.pharmacy_consultation_thank_you')
    
    @http.route('/pharmacy/consultation/submit', type='http', auth='public', website=True, methods=['POST'])
    def pharmacy_consultation_submit(self, **post):
        product_id = post.get('product_id')

        request.env['pharmacy.consultation.request'].sudo().create({
            'product_id': int(product_id) if product_id else False,
            'customer_name': post.get('customer_name'),
            'phone': post.get('phone'),
            'email': post.get('email'),
            'note': post.get('note'),
        })

        return request.redirect('/shop')