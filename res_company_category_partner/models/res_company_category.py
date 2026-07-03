# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models
from odoo.exceptions import ValidationError


class ResCompanyCategory(models.Model):
    _inherit = "res.company.category"

    def _can_create_root_category(self):
        """Only administrators may create or produce root categories."""
        return self.env.su or self.env.user.has_group("base.group_system")

    def _raise_root_category_error(self):
        raise ValidationError(
            self.env._(
                "Only administrators can create root company categories. "
                "Pick an existing parent category and create the new one "
                "as a leaf under it."
            )
        )

    @api.model_create_multi
    def create(self, vals_list):
        # This also blocks ``name_create`` (the many2one quick-create),
        # which creates a category with nothing but a name and would
        # silently make it a new root.
        if not self._can_create_root_category():
            for vals in vals_list:
                if not vals.get("parent_id"):
                    self._raise_root_category_error()
        return super().create(vals_list)

    def write(self, vals):
        # Emptying ``parent_id`` on an existing category would turn it into
        # a new root through the back door: same rule as in ``create``.
        if (
            "parent_id" in vals
            and not vals["parent_id"]
            and not self._can_create_root_category()
        ):
            self._raise_root_category_error()
        return super().write(vals)
