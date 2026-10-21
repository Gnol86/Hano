# Actions and notification lifecycle

Hano exposes three native Home Assistant actions. Their graphical fields are
available in the automation and script editors. English is the reference language;
French and Spanish translations include the action forms and panel.

| Action | Purpose | Response |
| --- | --- | --- |
| `hano.send` | Create, update, or start a new notification cycle | Optional notification record |
| `hano.preview` | Validate and calculate routing without sending or storing a cycle | Required response data |
| `hano.resolve` | Close an active notification and cancel its pending sends | Optional notification record |

Interactive calls require an administrator. Ordinary Home Assistant automation
contexts are supported. A preview performs the same target and option validation
as a send, but does not notify devices, create persistent notifications, or run
button actions.

## Send and preview fields

`message` is required. All other defaults are listed below. The same request fields
apply to both `send` and `preview`. Invalid field combinations fail before calls to
any destination. Runtime failures after sending starts remain independent per
destination.

### Content

| Field | Default | Meaning |
| --- | --- | --- |
| `notification_id` | Generated | Stable logical ID used for updates and resolution |
| `title` | Empty | Optional title; a generic `notify` entity must support titles |
| `message` | Required | Main text |
| `image_url` | Empty | Companion image URL or local path |
| `click_url` | Empty | Link opened when the notification is tapped |
| `camera_entity_id` | Empty | Existing `camera` entity: live attachment on iOS, snapshot on Android |
| `icon` | Empty | Notification icon, such as `mdi:washing-machine`; iOS requires a title |
| `color` | Empty | Hex notification color; iOS requires both an icon and a title |
| `timeout` | `0` | Android display timeout in seconds; `0` omits the option |

Display timeout is a device option. It does not replace Hano's cycle expiration.
Select either `image_url` or `camera_entity_id`, not both. Android camera snapshots
use the existing camera proxy endpoint; they are not live camera attachments.
Images accept HTTP, HTTPS, or local paths. Links can use supported app schemes;
executable or local-file URL schemes are rejected.

### Recipients and availability

| Field | Default | Meaning |
| --- | --- | --- |
| `recipient_mode` | `selected` | `selected`, `all`, `present`, `absent`, or `nearest` |
| `person_entity_ids` | `[]` | Configured people when using `selected` |
| `mobile_device_ids` | `[]` | Direct Companion devices, selected by HA device registry ID |
| `notify_entity_ids` | `[]` | Direct `notify` entities |
| `channels` | `[mobile]` | Any nonempty combination of `mobile`, `voice`, and `persistent` |
| `respect_sleep` | `true` | Require a configured sleep sensor to confirm wakefulness |
| `delivery` | `immediate` | `immediate` or `when_available` |
| `priority` | `normal` | `quiet`, `normal`, `important`, or `critical` |

Recipient modes refer only to residents configured in Hano:

- **`selected`** uses `person_entity_ids`; **`all`** uses all configured residents.
  These modes do not require being at home.
- **`present`** requires `person` state `home`; **`absent`** requires a known state
  other than `home`. Unknown and unavailable states are not considered absent.
- **`nearest`** chooses the closest eligible residents using person coordinates and
  the home location. A resident at home has distance zero. Ties are included, with
  a one-metre comparison tolerance. Missing or invalid coordinates produce a
  routing reason instead of a fallback broadcast. The nearest selection is fixed
  for the cycle once an eligible selection exists.

For the washing-machine pattern, use `present` with `when_available`: each resident
waits until both presence and wakefulness requirements are met. With `immediate`,
ineligible recipients are skipped for that cycle. With `when_available`, Hano
subscribes to the configured entities and sends only the pending destinations
when they become eligible.

Without a sleep sensor, no sleep condition is applied. A configured sleep sensor
uses `on` for asleep and `off` for awake. Unknown sleep state blocks an initial send
when sleep is respected. **Priority and sleep are independent**: choose
`respect_sleep: false` explicitly if the message should ignore sleep.

Direct device/entity recipients do not inherit a resident's sleep or presence
conditions. A destination shared by several selected residents is deduplicated and
becomes eligible when at least one of its selected owners is eligible.

The `mobile` channel includes Companion and generic `notify` destinations. The
`persistent` channel creates one Home Assistant persistent notification. Neither a
persistent notification nor a voice announcement marks a person as having read or
heard anything.

### Lifecycle

| Field | Default | Meaning |
| --- | --- | --- |
| `cycle_mode` | `update` | `update` or `new` |
| `expires_in` | `0` | Cycle lifetime in seconds; `0` means no expiration |
| `resolve_on_clear` | `false` | Resolve globally when a correlated mobile clearing event is received |

Every logical notification has a distinct cycle ID. Sending an unused ID creates
a cycle. Sending an active ID with `cycle_mode: update` updates content on already
accepted mobile/persistent destinations, updates pending content, preserves each
destination's progress, and does not replay voice. The same mobile tag is reused.
Sounds and replacement behavior are controlled by the mobile OS.

An update must retain the recipient mode, selected people, direct destinations,
channels, voice mode, and explicit speaker selection. To change that destination
shape, use `cycle_mode: new`. A new cycle resolves the previous active one before
creating fresh delivery state. A send after resolution also creates a new cycle.
An update recalculates expiration from that request's `expires_in`.

Pending sends survive restarts. Completed calls are not repeated merely because
Home Assistant restarted. An interrupted call whose outcome cannot be established
is recorded as unknown; immediate voice work interrupted by a restart is not
replayed. Hano does not retry failed or uncertain sends automatically.

Configuration and recipient mapping are captured when a cycle starts. Editing
people or rooms in the panel affects future cycles. Existing pending work keeps
its original mapping until resolution or expiration.

### Voice

| Field | Default | Meaning |
| --- | --- | --- |
| `voice_mode` | `explicit` | `explicit` speakers or `occupied` configured rooms |
| `media_player_entity_ids` | `[]` | Speakers for explicit mode |
| `tts_entity_id` | Panel default | Existing TTS engine entity |
| `tts_language` | Panel default | Optional language supported by the TTS engine |
| `voice_message` | Main `message` | Optional separate spoken text |
| `volume` | Unset | Native announcement volume, from `0` to `100` |

Include `voice` in `channels` to enable announcements. Voice destinations are
calculated immediately. Occupancy requires a configured occupancy sensor in state
`on`. Room sleep/silence is respected when `respect_sleep` is true, including when
a selected speaker is assigned to a silent room. Unknown occupancy or room sleep
states do not count as availability.

`delivery: when_available` defers mobile recipients, not voice. Announcements are
not replayed when a room becomes occupied later or when a pending resident wakes.
Each speaker has its own outcome.

Without `volume`, Hano calls the existing `tts.speak` action. Playback behavior
comes from the selected media player. With `volume`, the player must belong to the
Sonos integration and be explicitly selected in Hano's **Verified native announcement
volume** setting. Hano then uses `media_player.play_media` with `announce: true`
and native announcement volume. Other players or unverified Sonos players reject
this option. There is no timed volume restoration or generic music snapshot.

### Buttons

`buttons` defaults to an empty list. Add entries in the graphical object selector;
its **Actions** field uses Home Assistant's native sequence editor.

| Field | Default | Meaning |
| --- | --- | --- |
| `id` | Required | Unique local identifier for this button within the request |
| `label` | Required | Visible button label |
| `uri` | Empty | Link to open; mutually exclusive with actions and resolution |
| `actions` | `[]` | Native Home Assistant action sequence |
| `resolve` | `false` | Resolve after the sequence completes successfully |

A resolution-only button uses an empty action sequence with `resolve: true`. A
button can also emit a correlated Hano event without a sequence or resolution.
A URI button only opens its link: the OS does not confirm that operation to Hano,
so it cannot also execute a sequence or resolve the notification.

```yaml
action: hano.send
data:
  notification_id: ventilation_check
  title: Ventilation
  message: Start the ventilation and close this notification?
  recipient_mode: all
  buttons:
    - id: start_ventilation
      label: Start ventilation
      actions:
        - action: fan.turn_on
          target:
            entity_id: fan.example
      resolve: true
    - id: open_dashboard
      label: Open dashboard
      uri: /lovelace/ventilation
```

Sequences run through Home Assistant's script engine with the original action
author's context. A failed sequence is recorded and does not resolve the
notification. Callbacks must match the current cycle, a generated button token,
and an identified destination. Duplicate processing is blocked; each callback
button executes at most once per cycle, including when its sequence fails.
Buttons from an older cycle cannot act on a newer one.

The panel's test composer uses the native action selector when Home Assistant has
loaded it. Full graphical action authoring is always available in Home Assistant's
automation editor. The standalone demonstration cannot edit or run native action
sequences.

## Resolve

`hano.resolve` takes only a required `notification_id`:

```yaml
action: hano.resolve
data:
  notification_id: laundry_finished
```

Resolution is idempotent for an existing resolved cycle. It records the closed
state, cancels pending recipients, dismisses Hano's persistent notification, and
requests clearing on attempted Companion destinations. It waits for any in-flight
send before issuing remote clearing, preventing a late send from escaping the
clearing request. Removing a Hano persistent notification in Home Assistant also
resolves the corresponding cycle; startup restoration does not.

Generic `notify` integrations have no common remote-clear API. Their clearing
result is marked unsupported; the Hano cycle is still resolved. A previously
spoken announcement cannot be recalled.

A mobile swipe remains local by default. `resolve_on_clear: true` requires an
actual Companion clearing event with a correlatable destination identity. Hano
does not infer a global resolution from an unidentifiable tag alone. Notification
received/cleared reporting varies by app and OS; do not rely on iOS swipe reporting
as a universal lifecycle signal.

## Responses and events

To retain a generated identifier in a script, request a response:

```yaml
- action: hano.send
  data:
    message: Example notification
    recipient_mode: all
  response_variable: sent
- action: hano.resolve
  data:
    notification_id: "{{ sent.notification_id }}"
```

`send` and `resolve` return a public notification record when response data is
requested: logical ID, cycle ID, lifecycle status, content, timestamps, request,
destination outcomes, and history. Private callback tokens are excluded.
`preview` requires response data and returns:

- `preview: true` and the normalized `request`;
- `routing.persons`, with `person_id`, `eligible`, `reason`, and optional `distance`
  in metres;
- `routing.media_player_entity_ids` and `routing.reasons`;
- the selected `destinations`, with target and person ID.

```yaml
- action: hano.preview
  data:
    message: Preview only
    recipient_mode: present
    delivery: when_available
  response_variable: preview
```

A processed callback button emits **`hano_notification_action`**, after its action
sequence has completed or failed. Event data includes `notification_id`, `cycle_id`,
`button_id`, and `success`. No such event is emitted for a URI button.

```yaml
triggers:
  - trigger: event
    event_type: hano_notification_action
    event_data:
      notification_id: laundry_finished
      button_id: taken_care_of
      success: true
actions:
  - action: input_boolean.turn_on
    target:
      entity_id: input_boolean.laundry_handled
```

At execution, Hano provides `notification_id`, `cycle_id`, and `button_id` to its
script engine. However, Home Assistant renders templates inside service action
data **when `hano.send` runs**, including nested button sequences. A template in
that native action cannot directly refer to a future click's `cycle_id`, and
templates reading states there are evaluated at send time. For decisions that
must read state at click time, call a separately defined HA script, or use the
correlated event in another automation. The panel/WebSocket path does not perform
the automation editor's earlier template rendering. Choose one execution path
for a given side effect to avoid deliberately executing it twice.

## Capability limits

Buttons require the mobile channel. Persistent HA cards and voice announcements
cannot display the configured mobile buttons; requests containing buttons without
the mobile channel are rejected before any send.

| Capability | iOS Companion | Android Companion | Generic `notify` entity |
| --- | --- | --- | --- |
| Message | Yes | Yes | Yes |
| Title | Yes | Yes | Only with `TITLE` support |
| Image and tap link | Yes | Yes | Rejected |
| Camera entity | Live attachment | Snapshot | Rejected |
| Icon and hex color | Icon requires title; color requires icon and title | Yes | Rejected |
| Display timeout | Rejected | Yes | Rejected |
| Callback/link buttons | Yes | Up to three | Rejected |
| Rich priority | OS permission/settings apply | Channel/settings apply | Rejected |
| Remote clearing | Request supported; OS limits apply | Request supported; OS limits apply | Unsupported |
| Received/cleared confirmation | Depends on app/OS events | Correlated events when reported | Unsupported |

Hano maps quiet/normal/important/critical to iOS interruption levels. A critical
iOS alert requests a critical sound. Android important/critical sends request high
transport priority; critical uses `alarm_stream`, and quiet uses a low-importance
`Hano silent` channel. Existing Android channel settings and device permissions
remain authoritative. Priority never changes `respect_sleep` implicitly.
