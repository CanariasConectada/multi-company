import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Set access rule to support multi-company fields
    """
    # Change access rule. Deliberately ``user.company_ids`` (every company
    # the acting user actually belongs to) and NOT the bare ``company_ids``
    # eval-context variable (``self.env.companies``, only the ones
    # currently active in the company switcher): visibility must not
    # depend on which companies happen to be checked in that dropdown
    # right now. A user genuinely assigned to a company (e.g. an
    # administrator kept in sync by res_company_admin_sync) must be able
    # to read that company's own contact even with a narrower active
    # selection -- see partner_multi_company_restrict's own rule for the
    # same reasoning applied to the rule it adds on top of this one.
    rule = env.ref("base.res_partner_rule")
    rule.write(
        {
            "domain_force": (
                "['|', '|', ('partner_share', '=', False),"
                "('company_ids', 'in', user.company_ids.ids),"
                "('company_ids', '=', False)]"
            ),
        }
    )
    rule_partner_bank = env.ref("base.res_partner_bank_rule")
    rule_partner_bank.write(
        {
            "domain_force": (
                "['|', ('company_ids', 'in', user.company_ids.ids),"
                "('company_ids', '=', False)]"
            ),
        }
    )
    # Initialize m2m table for preserving old restrictions
    env.cr.execute(
        """
        INSERT INTO res_company_res_partner_rel
        (res_partner_id, res_company_id)
        SELECT id, company_id
        FROM res_partner
        WHERE company_id IS NOT NULL
        """
    )
    fix_user_partner_companies(env)


def fix_user_partner_companies(env):
    for user in env["res.users"].search([]):
        user_company_ids = set(user.company_ids.ids)
        partner_company_ids = set(user.partner_id.company_ids.ids)
        if not user_company_ids.issubset(partner_company_ids) and partner_company_ids:
            missing_company_ids = list(user_company_ids - partner_company_ids)
            user.partner_id.write(
                {"company_ids": [(4, company_id) for company_id in missing_company_ids]}
            )


def uninstall_hook(env):
    """Restore product rule to base value.

    Args:
        cr (Cursor): Database cursor to use for operation.
        rule_ref (string): XML ID of security rule to remove the
            `domain_force` from.
    """
    # Change access rule
    rule = env.ref("base.res_partner_rule")
    rule.write(
        {
            "domain_force": (
                "['|', '|', ('partner_share', '=', False),"
                "('company_id', 'in', company_ids),"
                "('company_id', '=', False)]"
            ),
        }
    )
    rule_partner_bank = env.ref("base.res_partner_bank_rule")
    rule_partner_bank.write(
        {
            "domain_force": ("[('company_id', 'in', company_ids + [False])]"),
        }
    )
