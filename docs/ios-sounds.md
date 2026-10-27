# Custom iOS notification sounds

`ios_sound` selects a sound file already available in Home Assistant Companion on
**every selected iPhone**. It does not upload a file, check installation, or extend
a short sound. Use the exact filename including `.wav`, `.caf`, or `.aiff`; URLs,
paths, control characters and surrounding spaces are rejected. Leave it empty to
keep the previous behavior, including the default critical sound.

Apple requires custom notification sounds to last **less than 30 seconds** and
to be present on the device. A missing or unsuitable sound can fall back to the
default; a valid filename in Hano is not proof that the file is installed.
See [Apple's sound requirements](https://developer.apple.com/documentation/usernotifications/unnotificationsound).

For importing a custom file, Companion documents **WAV, 32-bit float, 48 kHz**:

1. Put the file somewhere accessible in the iPhone's Files picker, such as iCloud
   Drive. Keep its exact filename.
2. On that iPhone, open Home Assistant → Settings → Companion app → Notifications
   → Sounds → **Import custom sound**, then select the file.
3. Confirm it appears in Companion's sounds list. Follow Companion's restart
   guidance if needed, then test with only the intended device selected.

The [Companion sound guide](https://companion.home-assistant.io/docs/notifications/notification-sounds/)
also documents file sharing and system-sound import. A system sound name is not
proof that it has already been imported into the app.

Example using a fictional configured recipient and a file imported beforehand:

```yaml
action: hano.send
data:
  notification_id: long_sound_test
  message: Test of the imported notification sound.
  recipient_mode: selected
  person_entity_ids: [person.example]
  channels: [mobile]
  priority: critical
  ios_sound: hano_alarm_25s.wav
  reminder_interval: 0
  reminder_limit: 0
```

Critical priority sends `push.sound` with `name: hano_alarm_25s.wav`, `critical: 1`
and `volume: 1.0`, as described in the
[Companion critical notification guide](https://companion.home-assistant.io/docs/notifications/critical-notifications/).
Normal and important priority send the filename as `push.sound`. Quiet priority,
Android and generic notification destinations reject this option before any send.
The mobile channel is required; optional voice/persistent channels can coexist.
Critical priority still respects Hano's sleep setting unless explicitly disabled.

One send requests one playback. Keep reminders disabled for a single long alert;
separate sends or explicit updates from an automation can sound again. Resolution
requests remote clearing but does not guarantee stopping a sound already playing.
Preview validates routing and options without sending or persisting a notification.
Neither preview nor an accepted service call proves that the intended sound was
heard. Confirm import, duration and actual playback on the selected phone before
changing a real alert workflow.
