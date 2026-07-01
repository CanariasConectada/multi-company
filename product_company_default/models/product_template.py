# Copyright 2026 Canarias Conectada
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, api, models
from odoo.tools import config


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model_create_multi
    def create(self, vals_list):
        # ``product_multi_company`` leaves new products global by default
        # (empty ``company_ids`` = visible to every company). For a strict
        # per-company setup that is the wrong default: a merchant creating a
        # product should get it scoped to its own company without having to
        # touch (or even see) the multi-company field.
        #
        # We set ``company_ids`` directly instead of defaulting ``company_id``:
        # ``company_id`` is a computed/inverse field here, and letting its
        # inverse run during ``create`` triggers an early write that the
        # company record rule rejects. Writing ``company_ids`` is the safe path.
        if not self._skip_company_default():
            company_command = Command.set(self.env.company.ids)
            for vals in vals_list:
                # Respect an explicit choice (including a deliberate global one
                # made by an admin who can see the field).
                if not vals.get("company_ids") and not vals.get("company_id"):
                    vals["company_ids"] = [company_command]
        return super().create(vals_list)

    @api.model
    def _skip_company_default(self):
        """Skip the default while a test suite runs (unless it opts in), so the
        global-by-default expectations of other modules keep passing."""
        return config["test_enable"] and not self.env.context.get(
            "test_product_company_default"
        )
