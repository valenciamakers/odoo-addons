Assign multiple email addresses to a contact, and Odoo matches mail from all of them.

In standard Odoo, a contact can have only one email address, and mail from another address is
treated as a unique sender, resulting in duplicate contacts. This module lets a contact have
additional email addresses, so mail from any of them is matched to the same contact record.

**Installation**

Install **Multiple Contact Emails** from the Apps menu. It only requires Odoo's **Discuss** module, and works on both Community and Enterprise.

**Using it**

Open a contact and go to the **Additional Emails** tab.

- **Add an email address** for each unique address the contact uses, with an optional label
  such as *Personal* or *Billing*. Drag the rows into any order.
- **Hover over an address** to show an envelope, which opens it in your own mail client.
- **Click the swap button** to swap an additional email address with the primary email. The old
  primary address is moved to the additional email addresses list.

Incoming mail from any of these email addresses is then matched to the contact, including mail that
creates a lead, an applicant, or a ticket in CRM, Recruitment, or Helpdesk. The resulting record
keeps the address the mail came from, and the contact's primary address is left as you set it.

Searching contacts by email, in the search bar or when selecting a contact in a form, finds any of
their addresses. **Merging two contacts** keeps both sets of addresses in the resulting contact.

**Limits**

- **Additional addresses are never mailed.** Odoo sends to the primary email address only.
- **Blacklisting, bounce counts, and mail-loop detection** read the primary email address only.
- **Merging contacts with different addresses** needs an administrator, as in standard Odoo.

**Changelog**

*18.0.1.0.1 (1 October 2026)*

- Browser tests added. No change in behaviour.

*18.0.1.0.0 (28 September 2026)*

- First release for Odoo 18, ported from 19.0.1.2.0. ``ban_emails``, ``filter_found``,
  ``no_create``, ``sort_key``, and ``sort_reverse`` are not available on
  ``_find_or_create_from_emails`` here: Odoo 18's own version of that method does not support
  them, so this module cannot offer them either.
