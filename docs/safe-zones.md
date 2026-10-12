# Safe zones

Safe zones are the named geofences a Guardian sets up **in the Xplora app** (e.g. "Home",
"School"). The **watch itself** checks whether it is inside one and reports the result with every
location update — the integration only relays that report, it never re-computes zone membership.
Safe zones are deliberately **not** Home Assistant zones: they stay Xplora-owned, and converting
them would affect every person/tracker in your Home Assistant instance.

Three kinds of entities surface them (all Guardian-only — see [Account types](account-types.md)):

- **`binary_sensor.<watch>_safezone`** — the in/out alert. It is a *safety* sensor, so **on means
  the watch is OUTSIDE every safe zone** (the alert state) and off means it is inside one.
  This is the only entity the **"Home is Safezone"** option affects: with it enabled, being
  within your Home Assistant home radius also counts as "inside", even if the watch itself
  reports otherwise.
- **`sensor.<watch>_current_safezone`** — the **name** of the safe zone the watch says it is in
  right now (disabled by default). While the watch is outside every safe zone the state is
  **unknown** — that is the normal "not in any zone" reading, **not** an error. The sensor is a
  pure watch report: "Home is Safezone" has no effect on it, and there is no fixed
  "outside"-style state that could collide with a zone you named yourself.
- **`device_tracker.<watch>_safezone_*`** — one per configured safe zone (disabled by default).
  These exist to draw the zone circles on the map: their coordinates are the zone's centre and
  their `gps_accuracy` its radius. The zone's own name is in the `safezone_name` attribute; the
  entity's *state* is computed by Home Assistant from the zone's coordinates (usually
  `not_home`, or the name of an HA zone covering that spot) — it does **not** show the Xplora
  zone name as the state.

The overview card's **Safe zone tile** combines the first two: it shows **Outside** when the
binary sensor alerts, the reported zone name while inside one (with the `current_safezone`
sensor enabled), and plain **Inside** when no zone name is known.

All of the above follow the watch's **location** reports, so they only change when Home Assistant
gets a fresh position. The watch also reports **arriving at and leaving** a safe zone to the
account's notification feed, the same source the app's alerts come from. Turn on the **Safe zones**
category to get these as `xplora_watch_safezone` events; see
[Call & notification activity](notifications.md).
