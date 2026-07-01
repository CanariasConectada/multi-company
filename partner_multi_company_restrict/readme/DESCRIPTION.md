This module tightens `partner_multi_company`'s company scoping on contacts.

Odoo's standard `res.partner` record rule always shows contacts linked to
an internal user (`partner_share = False`), regardless of company, so that
"assigned to" pickers and similar widgets keep working. On a multi-company
deployment where internal users belong to different companies, this means
a merchant without multi-company access can still see (and interact with)
the contact record of a colleague from another company.

This module adds a second, global record rule that removes that exemption
for users without the *Multi Companies* group: such a contact is only
visible if it also matches the normal company scoping (own company, or a
blank/shared company). Users with the *Multi Companies* group are
unaffected.

The restriction can be turned off from *Settings > General Settings >
Companies* if it breaks a legitimate cross-company use case, such as
adding a colleague as a follower on a shared document.
