This module restricts visibility of contacts linked to internal users
(colleagues), on top of `partner_multi_company`'s company scoping.

Odoo's standard `res.partner` record rule always shows contacts linked to
an internal user (`partner_share = False`), regardless of company, so that
"assigned to" pickers and similar widgets keep working. This means a
merchant can see (and interact with) the contact record of any colleague,
even one from a different company, or one they have no relationship with
at all -- distracting clutter at best, exposure of a colleague's personal
data at worst.

This module adds a second, global record rule: a user without the *Multi
Companies* group only sees a colleague's contact if at least one of these
holds:

- it is their own contact (the one linked to the account they are logged
  in as);
- they created it;
- it has been deliberately shared (blank *Companies*, the same convention
  used across this stack for "visible everywhere");
- it is not actually an internal user's contact in the first place (e.g. a
  portal customer), which is unaffected by this rule and keeps following
  the normal company scoping.

Users with the *Multi Companies* group are unaffected and keep seeing
every contact, as before.

The restriction can be turned off from *Settings > General Settings >
Companies* if it breaks a legitimate use case, such as adding a colleague
as a follower on a shared document.
