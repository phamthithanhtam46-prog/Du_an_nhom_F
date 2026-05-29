# -*- coding: utf-8 -*-
{
    'name': 'Module 6 - Pharmacy Sales',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Quản lý đơn thuốc nhà thuốc mở rộng từ phân hệ Bán hàng',
    'depends': ['sale_management', 'product'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/product_template_views.xml',
        'views/prescription_views.xml',
        'views/prescription_customer_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
