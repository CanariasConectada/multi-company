# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models
from odoo.exceptions import AccessError, UserError

MANAGER_GROUP = "res_company_category_partner.group_company_category_manager"


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Proxy over ``res.company.category_id`` for the partner that is the main
    # contact (``res.company.partner_id``) of a company. It lets members of
    # the "Company Category Manager" group classify a company straight from
    # its contact form, without access to Settings > Companies.
    company_category_id = fields.Many2one(
        comodel_name="res.company.category",
        string="Company Category",
        compute="_compute_company_category_id",
        inverse="_inverse_company_category_id",
        domain=[("type", "=", "normal")],
        # The value depends on *who* reads it (only companies among the
        # user's active companies are exposed), so it must not be computed
        # as sudo nor shared across users in the cache.
        compute_sudo=False,
        depends_context=("uid", "allowed_company_ids"),
        # Field-level gate: users outside the group can neither read nor
        # write the proxy, whatever the view says.
        groups=MANAGER_GROUP,
    )
    # Drives the view visibility (``invisible="not show_company_category"``):
    # only ON when the partner is the main contact of a company the user is
    # currently allowed to work in.
    show_company_category = fields.Boolean(
        compute="_compute_show_company_category",
        compute_sudo=False,
        depends_context=("uid", "allowed_company_ids"),
        groups=MANAGER_GROUP,
    )

    def _get_category_company_map(self):
        """Return ``{partner_id: res.company}`` for partners backing a company.

        The lookup is the inverse of ``res.company.partner_id``. It runs as
        sudo on purpose: record rules on ``res.company`` may hide the company
        from the current user, but visibility and writability are decided
        explicitly afterwards against ``self.env.companies``, so nothing
        foreign ever leaks.

        In this system a partner backs at most one company; if several
        companies ever pointed to the same partner, the oldest one (lowest
        ``id``) wins consistently for both read and write.
        """
        companies = (
            self.env["res.company"]
            .sudo()
            .search(
                [("partner_id", "in", self.ids)],
                order="partner_id, id",
            )
        )
        company_map = {}
        for company in companies:
            company_map.setdefault(company.partner_id.id, company)
        return company_map

    # No @api.depends: res.partner has no relational path towards the
    # companies it backs (base dropped ``ref_company_ids``), so the source
    # (``res.company.category_id``) is reached through a search instead.
    # The field is not stored and is cached per user/allowed-companies, so
    # it is recomputed whenever a fresh environment reads it; assignments
    # through the inverse keep the very cache that just wrote it coherent.
    def _compute_company_category_id(self):
        company_map = self._get_category_company_map()
        allowed = self.env.companies
        for partner in self:
            company = company_map.get(partner.id)
            if company and company in allowed:
                partner.company_category_id = company.category_id
            else:
                # Not a company's main contact, or a company outside the
                # user's active companies: expose nothing.
                partner.company_category_id = False

    def _inverse_company_category_id(self):
        company_map = self._get_category_company_map()
        allowed = self.env.companies
        for partner in self:
            company = company_map.get(partner.id)
            if not company:
                if partner.company_category_id:
                    raise UserError(
                        self.env._(
                            "%(partner)s is not the main contact of any "
                            "company, so no company category can be set "
                            "on it.",
                            partner=partner.display_name,
                        )
                    )
                continue
            # Server-side enforcement, mirroring the visibility rules: the
            # view alone must never be the only guard.
            if not self.env.su:
                if not self.env.user.has_group(MANAGER_GROUP):
                    raise AccessError(
                        self.env._(
                            'Only members of the "Company Category '
                            'Manager" group can change the category of a '
                            "company from its contact."
                        )
                    )
                if company not in allowed:
                    raise AccessError(
                        self.env._(
                            "You cannot change the category of company "
                            "%(company)s: it is not among your active "
                            "companies.",
                            company=company.name,
                        )
                    )
            # ``company`` is a sudo record: writing ``category_id`` on
            # ``res.company`` normally requires Administration rights, and
            # granting them is exactly what this module avoids. The
            # deliberate privilege escalation is safe because it is limited
            # to this single field and happens only after the group and
            # allowed-company checks above.
            company.category_id = partner.company_category_id

    def _compute_show_company_category(self):
        company_map = self._get_category_company_map()
        allowed = self.env.companies
        for partner in self:
            company = company_map.get(partner.id)
            partner.show_company_category = bool(company) and company in allowed
