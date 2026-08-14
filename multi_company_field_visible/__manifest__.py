# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Multi Company Field Visible",
    "summary": "Let non multi-company users manage their own company on records",
    "version": "19.0.2.1.0",
    "author": "Canarias Conectada, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "category": "Tools",
    "license": "AGPL-3",
    # ``mail`` for the ownership tracking: the chatter is where a merchant (or
    # whoever they ask) finds out who changed the companies on a record.
    "depends": ["base_multi_company", "mail"],
    "installable": True,
}
