# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html.html

from odoo import Command, api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        # Base ``res.users.create()`` syncs the partner's ``company_id``
        # mid-create ("if partner is global we keep it that way",
        # ``odoo/addons/base/models/res_users.py``) whenever the partner
        # already has a company -- an existing partner being promoted to
        # user, or any module putting a default on
        # ``res.partner.company_id`` (e.g. ``partner_company_default``).
        # That write fires the ``company_id`` inverse, which rewrites the
        # partner's ``company_ids`` down to a single company while the
        # user is only half-built, and ``_check_company_id`` would reject
        # that transient state before the alignment below ever runs. Skip
        # the constraint during the create; the alignment write below
        # re-triggers it on the final, consistent state.
        users = super(
            ResUsers, self.with_context(res_users_creation_in_progress=True)
        ).create(vals_list)
        users = users.with_context(res_users_creation_in_progress=False)
        for user in users:
            # The new user might have a company even if it was not in `vals`
            # because of defaults for example.
            if user.company_ids:
                user.partner_id.company_ids += user.company_ids
        return users

    def write(self, vals):
        res = super(ResUsers, self.with_context(from_res_users=True)).write(vals)
        if "company_ids" in vals:
            for user in self.sudo():
                partner = user.partner_id
                # Global partners (no company_ids) are visible everywhere on
                # purpose, so we never narrow them here.
                if not partner.company_ids:
                    continue
                user_company_ids = user.company_ids.ids
                if set(partner.company_ids.ids) != set(user_company_ids):
                    # Mirror the user's companies onto its contact card:
                    # grant the newly added ones AND revoke the removed ones.
                    # The previous implementation only ever linked companies,
                    # so a user pulled out of a company kept a contact card
                    # that stayed visible to that company. ``Command.set``
                    # reflects the revocation too. This runs *after*
                    # ``super().write`` so ``user.company_ids`` already holds
                    # the final set and the ``res.partner`` company constraint
                    # (partner companies must cover the user's) sees a
                    # consistent state for both additions and removals.
                    partner.company_ids = [Command.set(user_company_ids)]
        return res
