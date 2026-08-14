# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestProductOwnCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Opt this run into the "never blank" constraint (skipped by default
        # during tests so other modules keep their global-by-default checks).
        cls.env = cls.env(
            context=dict(cls.env.context, test_multi_company_field_visible=True)
        )
        cls.company_a = cls.env["res.company"].create({"name": "Field Visible A"})
        cls.company_b = cls.env["res.company"].create({"name": "Field Visible B"})
        # Merchant: a plain internal user owning a single company (so it does
        # NOT get base.group_multi_company).
        # A realistic merchant: can manage products, owns a single company
        # (so no base.group_multi_company) and cannot read other companies.
        cls.merchant_a = new_test_user(
            cls.env,
            login="fv_merchant_a",
            groups="base.group_user,product.group_product_manager",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.Product = cls.env["product.template"]

    def _product(self, company_ids):
        return self.Product.create(
            {"name": "FV Product", "company_ids": [(6, 0, company_ids)]}
        )

    def test_compute_shows_only_own_company(self):
        product = self._product((self.company_a + self.company_b).ids)
        as_merchant = product.with_user(self.merchant_a)
        self.assertEqual(as_merchant.own_company_ids, self.company_a)
        self.assertTrue(as_merchant.show_own_company_field)

    def test_inverse_preserves_hidden_companies(self):
        product = self._product((self.company_a + self.company_b).ids)
        product.with_user(self.merchant_a).own_company_ids = self.company_a
        # Company B (invisible to the merchant) must survive the edit.
        self.assertIn(self.company_b, product.company_ids)
        self.assertIn(self.company_a, product.company_ids)

    def test_never_blank_falls_back_to_own_company(self):
        product = self._product(self.company_a.ids)
        product.with_user(self.merchant_a).own_company_ids = False
        # Deliberately not an exact-set assertion: where
        # ``product_company_default`` is installed every product also carries
        # the default company, which this user cannot see and the inverse
        # therefore preserves as a hidden co-owner. What the fallback promises
        # is that the merchant's own company survives a blanking edit.
        self.assertIn(self.company_a, product.company_ids)

    def test_cannot_escalate_to_foreign_company(self):
        product = self._product(self.company_a.ids)
        # The merchant cannot even read company B, so assigning it fails closed.
        with self.assertRaises(AccessError):
            product.with_user(self.merchant_a).own_company_ids = self.company_b

    def test_multi_company_user_field_hidden(self):
        product = self._product(self.company_a.ids)
        admin = self.env.ref("base.user_admin")
        admin.write({"company_ids": [(4, self.company_b.id)]})
        self.assertTrue(admin.has_group("base.group_multi_company"))
        self.assertFalse(product.with_user(admin).show_own_company_field)

    def test_settings_toggle_hides_field(self):
        product = self._product(self.company_a.ids)
        param = self.env["ir.config_parameter"].sudo()
        param.set_param("multi_company_field_visible.product", "False")
        product.invalidate_recordset()
        self.assertFalse(product.with_user(self.merchant_a).show_own_company_field)
        param.set_param("multi_company_field_visible.product", "True")
        product.invalidate_recordset()
        self.assertTrue(product.with_user(self.merchant_a).show_own_company_field)

    def test_direct_blank_company_ids_raises_for_merchant(self):
        # The own_company_ids inverse quietly refills a blank selection, but
        # writing the raw company_ids to empty has no such fallback: the
        # create/write safety net (_check_own_company_kept) must reject a
        # non multi-company user leaving an exposed record global.
        product = self._product(self.company_a.ids)
        with self.assertRaises(ValidationError):
            product.with_user(self.merchant_a).company_ids = False

    def test_search_own_company_ids_scopes_out_foreign(self):
        # _search_own_company_ids mirrors a query on the proxy onto the real
        # company_ids, but scoped to the user's own companies, so it can never
        # surface a record the merchant does not co-own -- not even when the
        # query explicitly targets a foreign company.
        owned = self._product(self.company_a.ids)
        foreign = self.Product.sudo().create(
            {"name": "FV Foreign", "company_ids": [(6, 0, self.company_b.ids)]}
        )
        as_merchant = self.Product.with_user(self.merchant_a)
        self.assertIn(
            owned,
            as_merchant.search([("own_company_ids", "in", self.company_a.ids)]),
        )
        self.assertNotIn(
            foreign,
            as_merchant.search([("own_company_ids", "in", self.company_b.ids)]),
        )

    # ── The merchant must keep at least one of their own companies ──────────
    #
    # Reported on 2026-08-14: a merchant cleared the company on one of her own
    # products and it disappeared from her shop. The product was co-owned by
    # the platform company, so clearing hers left it valid, owned, and
    # invisible to her -- which is why nothing complained and why she could not
    # find it again to put it back.
    #
    # ``own_company_ids`` was already safe (its inverse falls back, see
    # ``test_never_blank_falls_back_to_own_company`` above), and writing
    # ``company_ids`` outright fails on access rules
    # (``test_cannot_escalate_to_foreign_company``). ``company_id`` was the way
    # through: a plain Many2one whose inverse replaces the whole set, while the
    # old guard only looked at writes that named ``company_ids``.

    def test_company_id_cannot_drop_the_merchants_own_company(self):
        """The reported hole, in one assertion."""
        product = self._product((self.company_a + self.company_b).ids)
        with self.assertRaises(ValidationError):
            product.with_user(self.merchant_a).company_id = False

    def test_the_message_names_the_company_to_put_back(self):
        """A blocked write has to say what to do about it.

        The merchant cannot see the co-owner that remains, so an error that
        only said "invalid" would leave them with a form they cannot fix.
        """
        product = self._product(self.company_a.ids)
        with self.assertRaises(ValidationError) as caught:
            product.with_user(self.merchant_a).company_id = False
        self.assertIn(self.company_a.name, str(caught.exception))

    def test_a_platform_administrator_may_still_clear_it(self):
        """Global records stay possible for the people who mean it."""
        product = self._product(self.company_a.ids)
        admin = self.env.ref("base.user_admin")
        self.assertTrue(admin.has_group("base.group_system"))
        product.with_user(admin).company_id = False
        self.assertFalse(product.company_ids)

    def test_server_side_code_is_not_blocked(self):
        """``sudo`` writes ownership the user could not write themselves.

        The display proxy's own inverse does exactly this, so blocking sudo
        would break the very field this module adds.
        """
        product = self._product(self.company_a.ids)
        product.with_user(self.merchant_a).sudo().company_ids = self.company_b
        self.assertEqual(product.company_ids, self.company_b)

    def test_editing_anything_else_is_untouched(self):
        """The rule only fires on writes that touch ownership.

        A merchant editing the name of a product that is global, or owned by
        somebody else, must not be told to fix a company they never touched.
        """
        product = self._product([])
        product.with_user(self.merchant_a).sudo().name = "Renamed, still global"
        self.assertFalse(product.company_ids)

    def test_the_change_lands_in_the_chatter(self):
        """Who took the product off the shop, and when.

        Without this the only trace of an ownership change is the write date,
        which says somebody edited something.
        """
        product = self._product(self.company_a.ids)
        # Settle the creation first. ``mail.thread`` discards tracking for a
        # record still being created, so an edit in the same precommit window
        # produces nothing -- which is right (creating something is not a
        # change to it) but is not the situation being tested: a merchant
        # editing a product that already exists.
        self.env.flush_all()
        self.env.cr.precommit.run()

        product.company_ids = self.company_a + self.company_b

        # Tracking is deferred: ``mail.thread`` registers ``_track_finalize``
        # on the cursor's precommit queue, so nothing is written until the
        # transaction flushes. Reading straight after the write would find
        # nothing and prove nothing.
        self.env.flush_all()
        self.env.cr.precommit.run()
        tracked = product.message_ids.tracking_value_ids.filtered(
            lambda value: value.field_id.name == "company_ids"
        )
        self.assertTrue(tracked, "an ownership change must be tracked")
