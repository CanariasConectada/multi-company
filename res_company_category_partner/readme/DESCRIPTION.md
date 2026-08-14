This module exposes the category of a company (`res.company.category_id`,
from the `res_company_category` module) on the contact form of the partner
that is the company's main contact (`res.company.partner_id`).

Members of the new **Company Category Manager** security group can classify
companies and create new leaf categories straight from the Contacts app,
without needing access to *Settings > Companies* or Administration rights.

Key rules, all enforced server-side:

- The field only shows up on partners that are the main contact of a
  company, and only when that company is among the user's active companies.
- Only members of the group can read or assign the category.
- Group members can create new categories, but only as leaves under an
  existing parent: creating new root categories stays an
  administrator-only operation.
