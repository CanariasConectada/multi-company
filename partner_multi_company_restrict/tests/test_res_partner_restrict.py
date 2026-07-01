# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPartnerRestrictCrossCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env["res.company"].create({"name": "Restrict Co A"})
        cls.company_b = cls.env["res.company"].create({"name": "Restrict Co B"})
        cls.merchant_a = new_test_user(
            cls.env,
            login="restrict_merchant_a",
            groups="base.group_user,base.group_partner_manager",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        # A regular colleague, SAME company as merchant_a: must stay visible,
        # this is normal Odoo behaviour and not touched by this module.
        cls.colleague_a = new_test_user(
            cls.env,
            login="restrict_colleague_a",
            groups="base.group_user",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.partner_colleague_a = cls.colleague_a.partner_id
        # A system administrator, SAME company as merchant_a: must be
        # hidden regardless of sharing a company.
        cls.admin_a = new_test_user(
            cls.env,
            login="restrict_admin_a",
            groups="base.group_system",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.partner_admin_a = cls.admin_a.partner_id
        # A regular internal user of company B: must be hidden (other
        # company), regardless of not being an administrator.
        cls.internal_user_b = new_test_user(
            cls.env,
            login="restrict_internal_b",
            groups="base.group_user",
            company_id=cls.company_b.id,
            company_ids=[(6, 0, cls.company_b.ids)],
        )
        cls.partner_b = cls.internal_user_b.partner_id

    def test_same_company_colleague_is_visible(self):
        # Normal Odoo behaviour, unaffected: colleagues of your own company
        # keep showing up in Contacts.
        self.assertEqual(
            self.partner_colleague_a.with_user(self.merchant_a).name,
            self.partner_colleague_a.sudo().name,
        )

    def test_same_company_admin_is_hidden(self):
        # The new restriction: a system administrator's contact is hidden
        # from regular users even within their own company.
        with self.assertRaises(AccessError):
            self.partner_admin_a.with_user(self.merchant_a).name  # noqa: B018
        found = (
            self.env["res.partner"]
            .with_user(self.merchant_a)
            .search([("id", "=", self.partner_admin_a.id)])
        )
        self.assertFalse(found)

    def test_other_company_regular_user_is_hidden(self):
        with self.assertRaises(AccessError):
            self.partner_b.with_user(self.merchant_a).name  # noqa: B018
        found = (
            self.env["res.partner"]
            .with_user(self.merchant_a)
            .search([("id", "=", self.partner_b.id)])
        )
        self.assertFalse(found)

    def test_own_contact_is_visible(self):
        partner_a = self.merchant_a.partner_id
        self.assertEqual(
            partner_a.with_user(self.merchant_a).name, partner_a.sudo().name
        )

    def test_shared_contact_is_visible(self):
        self.partner_b.sudo().company_ids = False
        self.assertEqual(
            self.partner_b.with_user(self.merchant_a).name,
            self.partner_b.sudo().name,
        )

    def test_system_admin_sees_everything(self):
        self.assertTrue(self.admin_a.has_group("base.group_system"))
        # Sees a colleague from another company...
        self.assertEqual(
            self.partner_b.with_user(self.admin_a).name, self.partner_b.sudo().name
        )
        # ...and another administrator too.
        other_admin = new_test_user(
            self.env,
            login="restrict_admin_b",
            groups="base.group_system",
            company_id=self.company_b.id,
            company_ids=[(6, 0, self.company_b.ids)],
        )
        self.assertEqual(
            other_admin.partner_id.with_user(self.admin_a).name,
            other_admin.partner_id.sudo().name,
        )

    def test_setting_toggle_disables_restriction(self):
        rule = self.env.ref(
            "partner_multi_company_restrict.res_partner_rule_restrict_cross_company"
        )
        rule.sudo().active = False
        try:
            found = (
                self.env["res.partner"]
                .with_user(self.merchant_a)
                .search([("id", "=", self.partner_admin_a.id)])
            )
            self.assertTrue(found)
        finally:
            rule.sudo().active = True
