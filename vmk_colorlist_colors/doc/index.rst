Change the colors (and their names) used for tags, kanban cards, and calendars.

In standard Odoo, you can give a tag, a kanban card, or a calendar one of eleven colors, but they
are fixed, and so are their names. This module lets you change any color, as well as rename them. An
edited color is used everywhere Odoo draws that color: tags, kanban cards, calendars, the
color picker itself, and the website.

**Installation**

Install **Custom Colors** from the Apps menu. It only requires Odoo's base module, and works on both
Community and Enterprise.

**Using it**

Open **Settings › General Settings**, and in the **Colors** section click **Edit Colors**. The list
shows Odoo's eleven colors.

- **Pick a color** with the color picker on its row. Picking Odoo's own color again removes the
  custom one.
- **Rename a color** by typing over its name, in each of your languages. A name is translatable like
  any other, so a name changed in one language shows only in that language, and in those with no
  name of their own.
- **The undo arrow** next to an edited color resets it to Odoo's default color and name for that
  slot, and **Reset to Defaults** resets all eleven, after asking. Both reload the page, so the
  change shows everywhere at once. A color picked or a name typed in the list shows elsewhere after
  the next reload.

A tag's and a color picker swatch's background and text are lighter and darker shades of its color,
worked out by Odoo's own formulas, just like the default colors. On Enterprise, dark mode draws your
colors the same way it draws the default colors: it darkens each one, so what dark mode shows is a
deeper version of the color you picked.

Only users with the **Settings** access right (**Administration › Settings**) can open the list.

**Colors some apps give a meaning**

Most colors are only what someone picked for a tag, a stage, or a calendar, and any of them can be
replaced. A few of Odoo's apps, though, set a record's color themselves, as a traffic light, and a
color replaced with one of another kind loses that meaning there. If you run any of these apps,
keep Red a red, Orange an orange, and Green a green, tuned to your palette:

- **Red**, something is wrong: in **Attendances**, a shift over 16 hours or a missed check-out; in
  **Helpdesk**, a failed SLA, and hours overspent on a ticket.
- **Orange**, a warning: in **Helpdesk**, hours used up; in **Gamification**, a failed goal.
- **Green**, all is well: in **Attendances**, checked in now; in **Helpdesk**, a reached SLA.
- **Purple**, done: a reached goal in **Gamification**.

Checked against Odoo 18 Community and Enterprise on 26 November 2026.

**Limits**

- **The slots stay as in core Odoo.** This module changes how each of the eleven colors looks and
  what it is called, not how many there are.
- **The No color slot is not editable.** Odoo draws it as an empty circle whatever its color, and
  gives it a meaning of its own: an event tag with no color isn't shown on the website.
- **A record keeps its color's slot.** A tag set to Teal before the change shows the new color in
  Teal's place, under its new name.

**Uninstalling** puts Odoo's own colors and names back.

**Languages**

English, Spanish, and Catalan. If any translation seems incorrect, please
`contact us <mailto:info@valenciamakers.es>`_ and we will fix it.

**Changelog**

*18.0.1.0.0 (26 November 2026)*

- First release.
