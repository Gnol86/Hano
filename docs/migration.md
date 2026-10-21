# Migrating from AppDaemon Notifier

This guide was prepared from the actual `Notifier.py` application, its AppDaemon
configuration, and seven automation callers inspected before Hano was created.
It is a migration plan, not an automatic converter. Installing Hano does not edit
Home Assistant configuration, disable AppDaemon or alter existing automations.
Examples below use fictional entity names; the private installation inventory is
kept out of the public repository.

## What changes

The inspected application consumes `NOTIFIER` events to send messages and
`NOTIFIER_DISCARD` events to clear tagged messages. It maintains waiting recipients
in memory and uses configured proximity sensors for nearest-person delivery.

Hano uses native `hano.send`, `hano.preview` and `hano.resolve` actions. Pending
recipients, current cycles and expiration are persisted. People are mapped to
devices and optional sleep entities in Hano's panel. Nearest-person routing uses
`person` coordinates and the home location, with no proximity entities to create.

| Notifier input or behavior | Hano equivalent |
| --- | --- |
| `NOTIFIER` event | `hano.send` action |
| `NOTIFIER_DISCARD` for a tag | `hano.resolve` with `notification_id` |
| `tag` | Stable `notification_id` |
| `send_to_person` | `recipient_mode: selected` and `person_entity_ids` |
| `send_to_all` | `recipient_mode: all` |
| `send_to_present` | `recipient_mode: present` |
| `send_to_absent` | `recipient_mode: absent` |
| `send_to_nearest` | `recipient_mode: nearest` |
| `send_to_when_present` | `recipient_mode: present`, `delivery: when_available` |
| `title`, `message` | Same fields |
| `image` | `image_url` |
| `click` | `click_url` |
| `camera` | `camera_entity_id` |
| `icon`, `color` | Same fields, checked for platform compatibility |
| `timeout` | Android display timeout; use `expires_in` for Hano lifecycle expiration |
| Critical send | `priority: critical`; choose `respect_sleep` separately |
| Persistent-until-event behavior | Keep the cycle active; a HA automation calls `hano.resolve` at the terminal event |
| Legacy callback/action buttons | Recreate explicit buttons with HA action sequences or react to `hano_notification_action` |

The exact spelling of a legacy application option should be checked against the
installed source again before conversion. Hano does not provide compatibility
listeners for the old events: enabling both systems cannot create a second Hano
send unless the automations explicitly call both.

## Seven inspected callers

All seven inspected automations used nearest-person delivery with title, message
and tag. Their triggers and conditions should remain in HA automations.

| Caller purpose | Migration action | Logical identifier relationship |
| --- | --- | --- |
| Fire alarm returns to normal | Send nearest-person recovery information | Its existing fire recovery tag |
| Flood alarm returns to normal | Send nearest-person recovery information | Its existing flood recovery tag |
| Intrusion alarm automatically arms | Send nearest-person state information | Shared intrusion-state tag |
| Intrusion alarm disarms on arrival | Send nearest-person state information | Shared intrusion-state tag |
| Intrusion departure/arrival windows | Send nearest-person state information | Shared intrusion-state tag |
| Intrusion state notifications | Send nearest-person state information | Shared intrusion-state tag |
| Intrusion operation fails | Send nearest-person failure information | Separate intrusion-failure tag |

The four intrusion state callers intentionally share an identifier. Decide whether
each transition should update the current card or start a new cycle. Use
`cycle_mode: new` when the transition must notify again; use `update` when it is a
content correction with the same destinations. A new cycle also permits another
voice announcement and another execution of its buttons.

The installation also contains direct alarm notifications outside Notifier. They
are not part of these seven callers and should not be changed as a side effect of
this migration. Priority alone never overrides Hano's sleep policy; review safety
alarm automations individually when they are intentionally migrated later.

## Graphical setup and preview

1. Install Hano as a HACS custom repository, choosing the stable release. Keep
   existing Notifier callers in service during setup.
2. In **Hano → People**, map each `person` to its Companion device(s). Add the
   actual sleep sensor if needed. Any suitable HA entity is allowed; no Hapo
   integration is required. Sleep `on` means asleep, `off` means awake.
3. In **Rooms & voice**, configure speakers and occupancy only if voice is needed.
   Select the existing TTS engine. Do not enable volume override until that exact
   speaker's native announcement behavior has been verified.
4. Save, then preview the equivalent request. Test home, away, sleeping and unknown
   states. Confirm nearest results without configuring proximity sensors.
5. Test a distinct notification ID on explicitly chosen devices. Verify clearing,
   button actions, pending behavior and phone-specific permissions before cutover.

An example replacing a nearest-person Notifier call:

```yaml
actions:
  - action: hano.send
    data:
      notification_id: example_alarm_state
      title: Alarm status
      message: The alarm is armed.
      recipient_mode: nearest
      channels: [mobile]
      respect_sleep: true
      delivery: immediate
      cycle_mode: new
```

All these fields can be entered through the action editor. No YAML editing is
required. Use `hano.preview` with the same fields and a response variable to inspect
destinations without sending.

## Cutover without double sends

Perform this separately from publishing or downloading the integration.

1. Re-read live versions, the Notifier source/configuration and all seven callers.
   Record any changes since the initial inspection. Back up the relevant HA and
   AppDaemon configuration and retain an export of the previous automation actions.
2. Prepare replacement actions as disabled test copies, or as edits held until the
   cutover. Do not activate a second copy of a live notification trigger.
3. Choose a quiet cutover window. For each caller, replace its old event action with
   the Hano action in one edit, preserving triggers, conditions and message
   templates. Verify one event path at a time. Never leave both send actions active.
4. Cancel or handle any known old Notifier waits before disabling it. Its in-memory
   queue is not imported into Hano. Resolve remaining old mobile cards using the
   old mechanism while it is still available.
5. Search all automation/script sources again for `NOTIFIER` and
   `NOTIFIER_DISCARD`. Only after the migrated paths have been verified should
   Notifier be disabled in AppDaemon. Do not stop other AppDaemon applications.
6. Validate Hano after a controlled HA restart: an accepted send must not repeat;
   a pending person should receive only after becoming eligible; resolution must
   cancel every remaining wait.

For rollback, first disable the corresponding Hano action paths, resolve their
active cycles, then restore the saved legacy actions and re-enable Notifier. Do
not run both implementations for the same trigger during rollback. Hano history
does not reconstruct Notifier's old in-memory queue.
