# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, new_test_user, tagged

MANAGER_GROUP = "res_company_category_partner.group_company_category_manager"


@tagged("post_install", "-at_install")
class TestResCompanyCategoryPartner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        Category = cls.env["res.company.category"]
        cls.root = Category.create({"name": "Test Trades", "type": "view"})
        cls.leaf = Category.create({"name": "Test Bakeries", "parent_id": cls.root.id})
        cls.company_a = cls.env["res.company"].create({"name": "Test Co Alpha"})
        cls.company_b = cls.env["res.company"].create({"name": "Test Co Beta"})
        cls.partner_a = cls.company_a.partner_id
        cls.partner_b = cls.company_b.partner_id
        cls.person = cls.env["res.partner"].create({"name": "Test Some Person"})
        # A category manager allowed to work in company A only
        cls.user_manager = new_test_user(
            cls.env,
            login="ccp_test_manager",
            groups=f"{MANAGER_GROUP},base.group_partner_manager",
            company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )
        # An internal user able to edit contacts but outside the group
        cls.user_plain = new_test_user(
            cls.env,
            login="ccp_test_plain",
            groups="base.group_user,base.group_partner_manager",
            company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )

    def _as_manager(self, record, companies=None):
        companies = companies or self.company_a
        return record.with_user(self.user_manager).with_context(
            allowed_company_ids=companies.ids
        )

    # Visibility -----------------------------------------------------------
    def test_show_flag_on_company_partner(self):
        partner = self._as_manager(self.partner_a)
        self.assertTrue(partner.show_company_category)

    def test_show_flag_hidden_on_plain_partner(self):
        person = self._as_manager(self.person)
        self.assertFalse(person.show_company_category)
        self.assertFalse(person.company_category_id)

    def test_show_flag_hidden_on_not_allowed_company(self):
        # Company B is not among the manager's active companies
        partner = self._as_manager(self.partner_b)
        self.assertFalse(partner.show_company_category)

    def test_category_hidden_on_not_allowed_company(self):
        self.company_b.category_id = self.leaf
        partner = self._as_manager(self.partner_b)
        # The company has a category, but the proxy must not reveal it
        self.assertFalse(partner.company_category_id)

    # Assignment -----------------------------------------------------------
    def test_manager_assigns_category(self):
        partner = self._as_manager(self.partner_a)
        partner.company_category_id = self.leaf
        self.assertEqual(self.company_a.category_id, self.leaf)
        self.assertEqual(partner.company_category_id, self.leaf)

    def test_manager_clears_category(self):
        self.company_a.category_id = self.leaf
        partner = self._as_manager(self.partner_a)
        partner.company_category_id = False
        self.assertFalse(self.company_a.category_id)

    def test_user_without_group_cannot_read(self):
        partner = self.partner_a.with_user(self.user_plain).with_context(
            allowed_company_ids=self.company_a.ids
        )
        with self.assertRaises(AccessError):
            _category = partner.company_category_id

    def test_user_without_group_cannot_write(self):
        partner = self.partner_a.with_user(self.user_plain).with_context(
            allowed_company_ids=self.company_a.ids
        )
        with self.assertRaises(AccessError):
            partner.company_category_id = self.leaf
        self.assertFalse(self.company_a.category_id)

    def test_write_rejected_on_not_allowed_company(self):
        # Active companies stay {A}; writing on B's contact must fail
        partner = self._as_manager(self.partner_b)
        with self.assertRaises(AccessError):
            partner.company_category_id = self.leaf
        self.assertFalse(self.company_b.category_id)

    def test_write_rejected_on_plain_partner(self):
        person = self._as_manager(self.person)
        with self.assertRaises(UserError):
            person.company_category_id = self.leaf

    # Category creation ----------------------------------------------------
    def test_manager_creates_leaf(self):
        category = (
            self.env["res.company.category"]
            .with_user(self.user_manager)
            .create({"name": "Test Butchers", "parent_id": self.root.id})
        )
        self.assertEqual(category.parent_id, self.root)

    def test_manager_cannot_create_root(self):
        with self.assertRaises(ValidationError):
            self.env["res.company.category"].with_user(self.user_manager).create(
                {"name": "Test Rogue Root"}
            )

    def test_manager_cannot_quick_create(self):
        # name_create is the code path behind the many2one quick-create
        with self.assertRaises(ValidationError):
            self.env["res.company.category"].with_user(self.user_manager).name_create(
                "Test Quick Root"
            )

    def test_manager_cannot_unparent_category(self):
        with self.assertRaises(ValidationError):
            self.leaf.with_user(self.user_manager).write({"parent_id": False})

    def test_admin_creates_root(self):
        admin = new_test_user(
            self.env,
            login="ccp_test_admin",
            groups="base.group_system",
        )
        category = (
            self.env["res.company.category"]
            .with_user(admin)
            .create({"name": "Test Admin Root", "type": "view"})
        )
        self.assertFalse(category.parent_id)
