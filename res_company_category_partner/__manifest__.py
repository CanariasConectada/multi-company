# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Company Category from Partner",
    "summary": "Assign a company's category from its main contact form",
    "version": "19.0.1.0.0",
    "category": "Partner Management",
    "author": "Odoo Community Association (OCA)",
    "maintainers": ["mikecolangelo"],
    "development_status": "Beta",
    "website": "https://github.com/OCA/multi-company",
    "license": "AGPL-3",
    "depends": [
        "res_company_category",
    ],
    "data": [
        "security/res_company_category_partner_security.xml",
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
    ],
    "demo": [
        "demo/res_company_category_partner_demo.xml",
    ],
    "installable": True,
}
