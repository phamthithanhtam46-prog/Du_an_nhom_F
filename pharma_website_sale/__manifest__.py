{
    'name': 'Hệ thống Website Bán thuốc',
    'version': '1.0',
    'summary': 'Website bán hàng cho nhà thuốc Minh Châu',
    'category': 'Website',
    'author': 'Nhóm F',

    'depends': [
        'website_sale',
        'website_sale_stock',
        'sale_management',
        'stock',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/website_sale_templates.xml',
        'views/consultation_request_views.xml',
    ],

    'installable': True,
    'application': False,
}