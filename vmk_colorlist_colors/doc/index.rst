Change the colors (and their names) used for tags, kanban cards, and calendars.

In standard Odoo, the eleven colors you can give a tag, a kanban card, or a calendar are fixed, and
so are their names. This module lets you change any of them to one of your own, such as your
brand's, and rename it. A changed color is used everywhere Odoo draws that color: tags and badges,
kanban cards, calendars, the color picker itself, and the website.

**Installation**

Install **Custom Colors** from the Apps menu. It requires nothing beyond Odoo's **Settings**, and
works on both Community and Enterprise.

**Using it**

Open **Settings › General Settings**, and in the **Colors** section click **Edit Colors**. The list
shows Odoo's eleven colors.

- **Pick a color** with the color picker on its row. Picking Odoo's own color again removes the
  custom one.
- **Rename a color** by typing over its name, in each of your languages. A name is translatable like
  any other, so a name changed in one language shows only in that language, and in those with no
  name of their own.
- **The undo arrow** at the end of a changed row puts back Odoo's color and name, and **Reset to
  Defaults** does it for all eleven, after asking. Both reload the page, so the change shows
  everywhere at once. A color picked or a name typed in the list shows elsewhere after the next
  reload.

A tag's border, background, and text are lighter and darker shades of its color. They are worked out
from your color the way Odoo worked out its own, and on Enterprise, dark mode gets shades of its
own.

Only users with the **Settings** access right (**Administration › Settings**) can open the list.

**Colors some apps give a meaning**

Most colors are only what someone picked for a tag, a stage, or a calendar, and any of them can be
replaced. A few of Odoo's apps, though, set a record's color themselves, as a traffic light, and a
color replaced with one of another kind loses that meaning there. If you run any of these apps,
keep Red a red, Orange an orange, and Green a green, tuned to your palette:

- **Red**, something is wrong: in **Attendances**, a shift over 16 hours or a missed check-out; in
  **Helpdesk**, a failed SLA, and hours overspent on a ticket.
- **Orange**, a warning: in **Helpdesk**, hours used up; in **Gamification**, a failed goal; in
  **ESG**, data out of date.
- **Green**, all is well: in **Attendances**, checked in now; in **Helpdesk**, a reached SLA.
- **Purple** and **Teal**, done or up to date: a reached goal in **Gamification** (Purple), and data
  up to date in **ESG** (Teal).

A few screens also draw a label in a fixed color: in **Point of Sale** for restaurants, a table in
Red and the selected course in Green; some ShipStation shipping labels; and a recipient in **Mail**
in Cyan. Checked against Odoo 20 Community and Enterprise on 12 November 2026.

**Limits**

- **The slots stay Odoo's.** This changes how each of the eleven colors looks and what it is called,
  not how many there are.
- **No color stays as it is.** Odoo draws it as an empty circle whatever its color, and gives it a
  meaning of its own: an event tag with no color isn't shown on the website.
- **A record keeps its color's slot.** A tag set to Teal before the change shows the new color in
  Teal's place, under its new name.

**Uninstalling** puts Odoo's own colors and names back.

**Languages**

English, Spanish, and Catalan. If any translation seems incorrect, please
`contact us <mailto:info@valenciamakers.es>`_ and we will fix it.

**Changelog**

*20.0.1.0.0 (25 November 2026)*

- First release.
