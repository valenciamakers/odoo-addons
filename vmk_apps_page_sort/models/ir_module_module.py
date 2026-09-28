# Copyright 2026 Valencia Makers, SL
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import models, tools
from odoo.tools import SQL

# ICU's root collation: case-insensitive at the first level, with accented letters beside their
# base letter, which is alphabetical order as a person means it in English, Spanish and Catalan.
ICU_COLLATION = "und-x-icu"


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    @tools.ormcache()
    def _vmk_name_collation(self):
        """ICU's root collation if this PostgreSQL has it, else None.

        ICU ships with the standard PostgreSQL packages and Docker images, but a
        server built without it has no such collation, and naming a missing one
        in ORDER BY is an error. Checked once per registry.
        """
        self.env.cr.execute(SQL("SELECT 1 FROM pg_collation WHERE collname = %s", ICU_COLLATION))
        return ICU_COLLATION if self.env.cr.fetchone() else None

    def _order_field_to_sql(self, alias, field_name, direction, nulls, query):
        """Order by the displayed name alphabetically, not in byte order.

        Odoo creates databases with ``LC_COLLATE 'C'``, so a plain ORDER BY on
        ``shortdesc`` compares bytes: ``CRM`` before ``Calendar``, and accented
        initials after ``Z``. Only ``shortdesc`` is affected; core never orders
        modules by it, so this reaches the two Apps views this module orders and
        nothing else. Without ICU it falls back to ``lower()``, which fixes case
        but not accents.

        The ``if query.groupby`` line mirrors what core's own
        ``_order_field_to_sql`` does for a many2one or a boolean field
        (``odoo/models.py``): extend the query's ``GROUP BY`` with the plain
        field expression so a later ``ORDER BY`` decorating it (here, with
        ``COLLATE`` or ``lower()``) stays valid under PostgreSQL's rule that an
        ungrouped expression must be a function of a grouped column. On 18,
        ``Query.groupby`` (``odoo/tools/query.py``) is a single SQL expression,
        not the list ``odoo/orm/query.py`` grew in 19 -- extending it means
        reassigning it, not appending.
        """
        if field_name != "shortdesc":
            return super()._order_field_to_sql(alias, field_name, direction, nulls, query)
        sql_field = self._field_to_sql(alias, field_name, query)
        if query.groupby:
            query.groupby = SQL("%s, %s", query.groupby, sql_field)
        collation = self._vmk_name_collation()
        if collation:
            key = SQL("%s COLLATE %s", sql_field, SQL.identifier(collation))
        else:
            key = SQL("lower(%s)", sql_field)
        return SQL("%s %s %s", key, direction, nulls)
