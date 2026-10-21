# Development and validation

Hano is a custom integration for Home Assistant 2026.10 or newer. Python runs the
engine; the Lit/TypeScript panel edits configuration and displays state. The engine
continues to work when no browser is open.

## Local toolchain

Use Python 3.14.2 or newer within the 3.14 series, `uv`, and Node.js 24.
Dependencies are pinned by `uv.lock` and `package-lock.json`.

```sh
uv sync --frozen
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen pytest
npm ci
npm run check
npm test
npm run build
```

The compiled `custom_components/hano/frontend/hano-panel.js` is committed alongside
its Lit dependency licences. Rebuild after source changes and verify a second build
produces the same file. The Home Assistant panel URL includes a hash of its content,
so a newly loaded integration serves the corresponding bundle instead of relying
on the browser's previous cached URL.

Python tests use a real Home Assistant test environment, fake notification/TTS
services, and socket restrictions. They must never depend on household credentials,
a real phone, or a speaker. Frontend tests use a DOM environment and mocked WebSocket
messages; they verify drafts, revision conflicts, routing controls, language changes,
permissions, native selector wiring, and separate preview/send actions.

## Standalone panel

After building, serve the repository locally:

```sh
python3 -m http.server 8099 --bind 127.0.0.1
```

Open `http://127.0.0.1:8099/frontend/dev.html`. Parameters include `lang=en|fr|es`,
`theme=dark`, and `clean=1` to hide demo controls for screenshots. All residents and
notifications are fictional. Calls are simulated and no Home Assistant connection
is made.

Check notification details, configuration drafts, save/discard behavior, preview,
mobile navigation, and the Home Assistant menu event. The demo acknowledges a menu
request without imitating Home Assistant's sidebar. Native action-sequence editing
requires the real Home Assistant frontend and is not simulated.

## Real Home Assistant validation

Run a separate local Home Assistant configuration with only test entities and fake
transports. Do not install the candidate integration into a household instance as
part of routine development.

Verify these paths against the actual frontend:

1. Add Hano through **Devices & services** and open the administrator panel.
2. Configure fictional people, sleep sensors, devices, rooms, and TTS defaults.
3. In the automation editor, choose `hano.send`, add a structured button, and add
   an action sequence without switching to YAML.
4. Run `hano.preview` with response data. Confirm it creates no notification or
   outgoing service call.
5. Use fake services to test immediate sends, individual waiting, resolution,
   expiration, restarts, updates, and a new cycle under the same logical ID.
6. Check the panel and action forms in English, French, and Spanish, including a
   regional locale, at desktop and mobile widths in both themes.
7. Verify a non-administrator cannot read Hano history or invoke privileged calls.

Do not call an accepted service invocation “delivery.” Browser checks establish UI
behavior; fake services establish software behavior; real device delivery requires
its own explicitly scoped test.

## Public boundaries

See [architecture](architecture.md) for data flow and [actions](actions.md) for the
public action contract. Configuration has a monotonically increasing revision.
The panel sends the revision with `hano/save`; a conflicting write is rejected.
Active cycles retain their configuration snapshot. Keep that behavior consistent
when changing models, routing, storage, or UI.

All translations must have English, French, and Spanish parity. Preserve custom
names and entity IDs when the locale changes. Public documentation stays in English.

Do not log messages, coordinates, callback tokens, device registration secrets, or
button action payloads. Diagnostic tests must continue checking redaction. Do not
introduce external push credentials or an additional notification cloud service.

## CI and releases

Validation runs Python checks, TypeScript/DOM tests, a reproducible panel build,
Hassfest, and HACS validation. The release workflow validates the tag against the
manifest, Python project and lockfile, and release notes before publication.

For a release, align the Python-format version in `manifest.json`, `pyproject.toml`,
and `uv.lock`, add `releases/<version>.md`, rebuild the panel, run all checks, and tag
`v<version>`. `0.1.0b1` is the Python/Home Assistant version; the private npm project
uses its SemVer equivalent `0.1.0-beta.1`. Beta tags are published as prereleases.

Publication, HACS download, Home Assistant restart, and verified device behavior
are separate steps. This project does not submit itself to the default HACS
catalogue and does not automatically migrate or disable an existing Notifier app.
