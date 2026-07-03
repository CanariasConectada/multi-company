1. Open the Contacts app and pick the contact of a company (the partner
   linked as main contact of a `res.company`).
2. A **Company Category** field appears next to the tags. Pick a category:
   it is stored on the company itself (`res.company.category_id`).
3. To add a new category, use *Search More... / Create and edit...* in the
   drop-down (quick-create is disabled on purpose) and set a **Parent
   Category**: non-administrators must always create categories under an
   existing parent.

The field is hidden on regular partners (persons, standalone contacts) and
on company contacts whose company is not among your active companies. Any
attempt to bypass the UI (e.g. through RPC) is rejected by the server with
the same rules.

If several companies ever pointed to the same partner, the oldest company
(lowest database id) is the one read and written; this system expects one
company per partner.
