# Hano panel

The Lit panel inherits Home Assistant's active theme and locale (English, French,
Spanish, including regional variants). It uses administrator-only WebSocket
commands and does not run the notification engine in the browser.

## Develop and verify

Use Node.js 24. Run `npm ci`, `npm run check`, `npm test`, and `npm run build`
from the repository root. The committed bundle lives in
`custom_components/hano/frontend/hano-panel.js`; rebuild it whenever sources
change. Its dependency licences are distributed beside it.

Serve the repository with `python3 -m http.server 8099 --bind 127.0.0.1` and open
`http://127.0.0.1:8099/frontend/dev.html`. The standalone demo uses fictional
residents and simulated calls only. Query parameters: `lang=en|fr|es`,
`theme=dark`, and `clean=1` to hide demo controls when taking screenshots.
The demo does not contact a Home Assistant instance.

Entity fields use Home Assistant's native picker when it is registered and
accessible labelled selectors otherwise. Button action sequences use the native
Home Assistant action selector; in standalone mode they are not executable or
editable. For complete automation authoring use Hano's graphical action forms
inside Home Assistant's automation editor.

The configuration draft survives tab changes and live status updates. Saving
acknowledges only the submitted values; edits made during the request remain
unsaved. A concurrent server revision blocks saving until the draft is discarded.
Tests and manual commands are disabled while a configuration draft exists.
