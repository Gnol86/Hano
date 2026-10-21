# Contributing to Hano

Hano is an independent Home Assistant notification integration. Automations own
triggers, message content, recipients, and options; Hano owns delivery tracking,
individual waiting, persistence, and resolution. Do not introduce notification
profiles or dependencies on AppDaemon, Hapo, or `proximity` entities.

Before proposing a change, read the [action contract](docs/actions.md),
[architecture](docs/architecture.md), and [development guide](docs/development.md).

## Issues

Include the Hano and Home Assistant versions, the action/configuration involved,
expected and observed behavior, and whether a status is merely an accepted call or
a device-reported event. Use fictional names and redact message content, locations,
entity IDs, and device identifiers as appropriate. Hano's diagnostic export is
redacted; review any additional logs or screenshots before sharing them.

For delivery issues, identify the notification integration and platform. A failing
mobile delivery and a failing Hano routing decision are different observations.
Do not post registration credentials, access tokens, or raw Home Assistant storage.

## Pull requests

- Keep routing, persistence, adapters, and Home Assistant interfaces separate.
- Preserve pending recipients across restarts and protect against stale button
  callbacks, duplicate actions, and sends racing with resolution.
- Reject unsupported transport options before starting a send.
- Keep English, French, and Spanish translations complete. Preserve custom names.
- Include focused tests for behavior that changes, especially lifecycle races and
  permission boundaries. Keep ordinary UI configuration usable without YAML.
- Rebuild and commit the frontend bundle when its sources change; retain licences.
- Update public documentation in English to describe the implemented behavior and
  its limits.

Run the commands in [Development](docs/development.md) before submitting a pull
request. Do not perform tests against a household instance or physical device
unless that separate test is explicitly authorized.

Describe the concrete behavior changed, relevant validation, and remaining limits.
Use a small, reviewable change rather than combining unrelated refactors.

Contributions are provided under the repository's [MIT licence](LICENSE).
