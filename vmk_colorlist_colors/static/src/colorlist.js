// Copyright 2026 Valencia Makers, SL
// License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html).

import { ColorList } from "@web/core/colorlist/colorlist";
import { session } from "@web/session";

// The colors renamed in Settings, in the user's language, from the session
// (models/ir_http.py). Changed in place, since other modules keep a reference
// to the array itself: the kanban record takes `const { COLORS } = ColorList`
// when it loads.
for (const [slot, name] of Object.entries(session.vmk_colorlist_names || {})) {
    ColorList.COLORS[Number(slot)] = name;
}
