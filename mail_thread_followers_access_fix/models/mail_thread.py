# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _compute_message_partner_ids(self):
        for thread in self:
            follower_partner_ids = thread.sudo().message_follower_ids.partner_id.ids
            # A bare browse() would carry every follower id regardless of
            # whether the current user can actually read it. Odoo's field
            # conversion later checks each one's `active` field to build
            # the recordset, which enforces record rules and raises an
            # AccessError the instant a follower isn't readable (e.g.
            # hidden by a company- or role-based partner visibility rule),
            # crashing the read for the whole document. search() applies
            # those same rules up front and just omits what the user can't
            # see, instead of failing outright.
            thread.message_partner_ids = self.env["res.partner"].search(
                [("id", "in", follower_partner_ids)]
            )

    def _inverse_message_partner_ids(self):
        # Same fix as _compute_message_partner_ids, applied to the
        # "previous followers" side of the diff this inverse computes, so
        # that editing followers on a document with an unreadable one does
        # not crash either.
        to_unsubscribe = []
        for thread in self:
            new_partners_ids = thread.message_partner_ids
            # ``message_follower_ids`` read through sudo() also returns
            # followers hidden from the current user by partner-visibility
            # rules (e.g. another company's contacts). Those never appear in
            # ``message_partner_ids`` (built with a rule-aware search), so
            # diffing the new set against the *full* sudo set would classify
            # every hidden follower as "removed" and silently unsubscribe
            # followers the editor cannot even see. Restrict the "previous"
            # side to the partners the user is actually allowed to see, so
            # hidden followers are left untouched.
            previous_all_ids = thread.sudo().message_follower_ids.partner_id.ids
            previous_partners_ids = self.env["res.partner"].search(
                [("id", "in", previous_all_ids)]
            )
            removed_partners_ids = previous_partners_ids - new_partners_ids
            added_partners_ids = new_partners_ids - previous_partners_ids
            if added_partners_ids:
                thread.message_subscribe(added_partners_ids.ids)
            if removed_partners_ids:
                to_unsubscribe.append((thread, removed_partners_ids.ids))
        for thread, partner_ids in to_unsubscribe:
            thread.message_unsubscribe(partner_ids)
