# Architecture and lifecycle

Hano is one config-entry integration, with one durable engine per Home Assistant
installation. The panel is a client of that engine; closing the browser has no
effect on pending notifications.

## Components

| Module | Responsibility |
| --- | --- |
| `models.py` | Strict, JSON-compatible configuration and action validation |
| `routing.py` | Pure decisions from a snapshot of HA states and the home position |
| `manager.py` | Identity, cycles, transactions, subscriptions, expiration and history |
| `adapters.py` | Companion, generic notify, persistent notifications and TTS |
| `services.py` | Native actions and response contracts |
| `websocket.py` | Administrator-only panel commands and subscriptions |
| `panel.py` | Bundled panel registration with a content-hash URL |
| `diagnostics.py` | Allow-listed aggregate diagnostics |
| `frontend/` | Lit/TypeScript interface and simulated development fixture |

The engine does not implement automation triggers, profiles, reminders or an
escalation scheduler. It calls existing HA integrations, never vendor APIs.

## Identity and transactions

A logical `notification_id` can have several sequential `cycle_id` values. The
mobile tag contains the installation ID, a hash of the logical ID and the cycle.
An update keeps that tag; a new cycle gets another tag. Completed previous cycles
remain in history until retention or an explicit purge removes them.

State is written through Home Assistant `Store`, using atomic file writes, under
`.storage/hano.<entry_id>`. Every transport attempt has a persisted intent before
the external service call. A failed storage write rolls back the in-memory
transaction and prevents the following effect. This is not a distributed
transaction with mobile operating systems: a crash after an external effect can
leave its result unknown.

Per-notification locks serialize transport, replacement and clearing. Resolution
first records a terminal state and cancels pending destinations. It then waits
for an in-flight attempt before requesting clearing, so that a late successful
send is also cleared. New cycles wait for previous clearing operations to finish.
Callbacks carry the expected cycle, and a delayed callback cannot resolve a
replacement cycle.

## Destinations and availability

Each distinct mobile transport/target has one delivery row. Several configured
people can share that row; one eligible owner is enough to send it. Explicit
device destinations do not infer an owner's presence or sleep. Multiple devices
for one person each have their own row and result.

Selected/all modes do not require a location. Present/absent modes require a known
matching presence state. A configured sleep sensor must be `off` to confirm
wakefulness when sleep is respected. Unknown is never silently treated as home
or awake.

Nearest routing uses Haversine distance from `person` coordinates to the HA home
location. A person at home is at zero distance. Candidates with missing or invalid
coordinates are explained explicitly. Among eligible candidates, distances within
one metre of the minimum are treated as ties. Once a cycle has selected its
nearest eligible recipients, it does not chase moving people and expand to new
recipients. There is no `proximity` dependency.

Entity state subscriptions re-evaluate pending deliveries. Changes arriving while
an evaluation is running cause another pass. A periodic maintenance pass handles
expiration, retention and recovery from missed state notifications. Delivery
eligibility is checked again immediately before each attempt.

Voice destinations are calculated for the immediate call and never queued for a
later arrival or wake-up. Occupancy and room silence/sleep are checked before each
announcement. A voice attempt does not change a person's mobile delivery state.

## Restart and uncertainty

- Accepted mobile sends are not replayed.
- Mobile sends still waiting for availability resume waiting, then send only when
  eligible.
- Interrupted sending/updating/clearing operations become `unknown`.
- Voice that was not started before interruption is skipped, not replayed.
- Hano persistent cards are recreated for active cycles. Only removal callbacks
  resolve cycles; startup/current-state callbacks do not.
- Interrupted button sequences are not automatically executed again.

Hano records observed facts: the HA call returned, a correlated device callback
arrived, an error occurred, or clearing was requested. Companion's underlying
service can log provider failures without raising them; therefore even an accepted
HA call is not evidence of successful push delivery. No state claims that a human
read or heard a message.

## Buttons and authority

Every non-URL button gets an unpredictable token scoped to the cycle and mobile
destination. The handler checks token, cycle, destination identity and the
registered user where available. A button ID can execute once per cycle, even
when several devices display it; this prevents duplicated household actions.
Updating the card rotates tokens but does not reset already claimed button IDs.

Configured actions are validated and run by the HA script engine with the author
context, not authority taken from a phone's event payload. Interactive authors
must remain active administrators. Automation contexts retain their normal HA
authority. A script failure leaves the notification unresolved. Resolution stops
other running button scripts for that cycle; a script resolving itself can finish
its own clear operation. An already completed external action cannot be undone.

The `hano_notification_action` event contains the logical ID, cycle, button ID and
success result. It contains no message or location. Native URL buttons have no
execution callback and cannot request resolution after opening the link.

## Privacy and maintenance

Panel commands, live snapshots and full history require administrator access.
The static JavaScript bundle contains no installation data. Diagnostics return
aggregate counts only, excluding messages, actions, identifiers and positions.
Stored content remains part of HA's local storage and backups.

History retention defaults to 30 days and accepts 1–3650 days. Active cycles are
kept. Explicit purge removes completed history, retaining a cycle whose clearing
operation is still running until that operation completes. Each cycle keeps up
to its latest 1000 history entries. Configuration revisions prevent silent
overwrite of concurrent edits; an active cycle keeps its original destination
mapping even when configuration changes.
