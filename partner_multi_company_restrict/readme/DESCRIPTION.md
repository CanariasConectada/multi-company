This module restricts visibility of contacts linked to internal users
(colleagues) from another company, and of any system administrator's
contact, on top of `partner_multi_company`'s company scoping.

Odoo's standard `res.partner` record rule always shows contacts linked to
an internal user (`partner_share = False`), regardless of company, so that
"assigned to" pickers and similar widgets keep working. This means a
merchant can see (and interact with) the contact record of any colleague,
even one from a different company -- or an administrator account they
have no business seeing.

This module adds a second, global record rule: a user without the
*Administration / Settings* group only sees a colleague's contact if at
least one of these holds:

- it belongs to their own company (the normal, unrestricted case: seeing
  colleagues of your own company keeps working exactly as before);
- it is their own contact (safety net);
- it has been deliberately shared (blank *Companies*, the same convention
  used across this stack for "visible everywhere");
- it is not actually an internal user's contact in the first place (e.g. a
  portal customer), which is unaffected by this rule and keeps following
  the normal company scoping.

Regardless of company, a contact linked to a system administrator
(`base.group_system`) is always hidden from a regular user, since that
group is what actually manages users and configuration across companies.

Administrators (`base.group_system`) are unaffected and keep seeing every
contact, as before.

The restriction can be turned off from *Settings > General Settings >
Companies* if it breaks a legitimate use case, such as adding a colleague
as a follower on a shared document.
