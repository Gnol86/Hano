import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import { Window } from "happy-dom";
import { emptyConfig, emptyRequest } from "../src/model";
import type { Hass, Snapshot, Request } from "../src/types";
const window = new Window({ url: "http://localhost:8123" });
for (const key of [
  "window",
  "document",
  "customElements",
  "HTMLElement",
  "Element",
  "Node",
  "Document",
  "ShadowRoot",
  "CSSStyleSheet",
  "Event",
  "CustomEvent",
  "KeyboardEvent",
  "FocusEvent",
] as const)
  Object.defineProperty(globalThis, key, {
    configurable: true,
    value: key === "window" ? window : window[key],
  });
const { HanoPanel } = await import("../src/hano-panel");
type Panel = InstanceType<typeof HanoPanel>;
function fixture(): Snapshot {
  return {
    version: "0.1.0",
    revision: 1,
    config: {
      ...emptyConfig(),
      persons: [
        {
          person_id: "person.alex",
          name: "Alex",
          sleep_entity_id: "binary_sensor.alex_sleep",
          devices: [],
        },
      ],
      rooms: [],
    },
    notifications: [
      {
        notification_id: "washer",
        cycle_id: "cycle-one",
        status: "active",
        title: "Laundry finished",
        message: "The laundry can be removed.",
        created_at: "2026-10-21T14:00:00Z",
        updated_at: "2026-10-21T14:00:00Z",
        resolved_at: null,
        expires_at: null,
        request: emptyRequest(),
        deliveries: [
          {
            key: "mobile-a",
            person_id: "person.alex",
            channel: "mobile",
            target: "notify.mobile_app_alex",
            status: "pending",
            reason: "sleeping",
            updated_at: "2026-10-21T14:00:00Z",
          },
        ],
        history: [{ at: "2026-10-21T14:00:00Z", event: "created" }],
      },
    ],
    catalog: {
      entities: [
        {
          entity_id: "person.alex",
          name: "Alex",
          domain: "person",
          state: "home",
        },
        {
          entity_id: "binary_sensor.alex_sleep",
          name: "Sleep",
          domain: "binary_sensor",
          state: "on",
        },
        {
          entity_id: "media_player.living_room",
          name: "Living room",
          domain: "media_player",
          state: "idle",
        },
        {
          entity_id: "tts.local",
          name: "Local voice",
          domain: "tts",
          state: "unknown",
        },
        {
          entity_id: "notify.house",
          name: "House",
          domain: "notify",
          state: "unknown",
        },
      ],
      mobile_services: [
        {
          service: "notify.mobile_app_alex",
          name: "Alex phone",
          device_id: "device-a",
          platform: "ios",
        },
      ],
      mobile_devices: [
        {
          service: "notify.mobile_app_alex",
          name: "Alex phone",
          device_id: "device-a",
          platform: "ios",
        },
      ],
      areas: [{ area_id: "living_room", name: "Living room" }],
    },
  };
}
async function settle(panel: Panel) {
  await new Promise((resolve) => setTimeout(resolve, 5));
  await panel.updateComplete;
}
async function mount(
  options: {
    admin?: boolean;
    locale?: string;
    save?: (message: Record<string, unknown>) => Promise<Snapshot>;
  } = {},
) {
  let snapshot = fixture();
  let emit: (value: Snapshot) => void = () => {};
  const calls: Record<string, unknown>[] = [];
  let subscriptions = 0,
    unsubscriptions = 0;
  const hass: Hass = {
    user: { is_admin: options.admin ?? true },
    language: options.locale ?? "fr-BE",
    connection: {
      async subscribeMessage<T>(callback: (value: T) => void) {
        subscriptions++;
        emit = callback as (value: Snapshot) => void;
        emit(snapshot);
        return () => {
          unsubscriptions++;
        };
      },
    },
    async callWS<T>(message: Record<string, unknown>) {
      calls.push(structuredClone(message));
      if (message.type === "hano/save") {
        if (options.save) return (await options.save(message)) as T;
        snapshot = {
          ...snapshot,
          revision: snapshot.revision + 1,
          config: structuredClone(message.config) as Snapshot["config"],
        };
        emit(snapshot);
        return snapshot as T;
      }
      return {
        persons: [
          { person_id: "person.alex", eligible: false, reason: "sleeping" },
        ],
      } as T;
    },
  };
  const panel = new HanoPanel();
  panel.hass = hass;
  document.body.append(panel);
  await settle(panel);
  return {
    panel,
    hass,
    calls,
    emit: (value: Snapshot) => emit(value),
    snapshot: () => snapshot,
    counts: () => ({ subscriptions, unsubscriptions }),
  };
}
function buttons(panel: Panel) {
  return [...panel.shadowRoot!.querySelectorAll<HTMLButtonElement>("button")];
}
function click(panel: Panel, text: string) {
  const button = buttons(panel).find(
    (button) => button.textContent?.trim() === text,
  );
  assert.ok(button, `button ${text} exists`);
  button.click();
}
function input(panel: Panel, key: string, value: string) {
  const element = panel.shadowRoot!.querySelector<HTMLInputElement>(
    `[data-field="${key}"]`,
  );
  assert.ok(element, `input ${key} exists`);
  element.value = value;
  element.dispatchEvent(new Event("input", { bubbles: true }));
  return element;
}
function select(panel: Panel, key: string, value: string) {
  const element = panel.shadowRoot!.querySelector<HTMLSelectElement>(
    `[data-field="${key}"]`,
  );
  assert.ok(element);
  element.value = value;
  element.dispatchEvent(new Event("change", { bubbles: true }));
  return element;
}
afterEach(() => document.body.replaceChildren());
test("subscribes once and renders translated status detail", async () => {
  const { panel, counts } = await mount();
  assert.equal(counts().subscriptions, 1);
  click(panel, "Laundry finishedwasherEn attente");
  await settle(panel);
  assert.match(panel.shadowRoot!.textContent!, /Endormi/);
  assert.match(panel.shadowRoot!.textContent!, /Un appel accepté ne confirme/);
  assert.match(panel.shadowRoot!.textContent!, /Sans expiration/);
});
test("non-admin never subscribes or renders private content", async () => {
  const { panel, counts } = await mount({ admin: false });
  assert.equal(counts().subscriptions, 0);
  assert.match(panel.shadowRoot!.textContent!, /administrateur/);
  assert.doesNotMatch(panel.shadowRoot!.textContent!, /Laundry/);
});
test("admin loss clears private snapshot and draft", async () => {
  const { panel, hass, counts } = await mount();
  click(panel, "Personnes");
  await settle(panel);
  input(panel, "name", "Changed");
  panel.hass = { ...hass, user: { is_admin: false } };
  await settle(panel);
  assert.match(panel.shadowRoot!.textContent!, /administrateur/);
  assert.equal(panel.shadowRoot!.querySelector(".savebar"), null);
  assert.equal(counts().unsubscriptions, 1);
});
test("disconnect unsubscribes", async () => {
  const { panel, counts } = await mount();
  panel.remove();
  assert.equal(counts().unsubscriptions, 1);
});
test("draft survives navigation and server status refresh", async () => {
  const { panel, emit } = await mount();
  click(panel, "Personnes");
  await settle(panel);
  input(panel, "name", "Custom resident");
  await settle(panel);
  click(panel, "Pièces et voix");
  await settle(panel);
  emit(fixture());
  click(panel, "Personnes");
  await settle(panel);
  assert.equal(
    panel.shadowRoot!.querySelector<HTMLInputElement>("[data-field=name]")!
      .value,
    "Custom resident",
  );
  assert.ok(panel.shadowRoot!.querySelector(".savebar"));
});
test("save sends exact configuration revision and clears unchanged draft", async () => {
  const { panel, calls } = await mount();
  click(panel, "Personnes");
  await settle(panel);
  input(panel, "name", "Sam");
  await settle(panel);
  click(panel, "Enregistrer");
  await settle(panel);
  assert.equal(calls[0].type, "hano/save");
  assert.equal(calls[0].revision, 1);
  assert.equal((calls[0].config as Snapshot["config"]).persons[0].name, "Sam");
  assert.equal(panel.shadowRoot!.querySelector(".savebar"), null);
});
test("edits during save remain dirty after acknowledgement", async () => {
  let resolveSave!: (value: Snapshot) => void;
  let sent!: Record<string, unknown>;
  const { panel } = await mount({
    save: (message) => {
      sent = message;
      return new Promise((resolve) => (resolveSave = resolve));
    },
  });
  click(panel, "Personnes");
  await settle(panel);
  input(panel, "name", "First");
  await settle(panel);
  click(panel, "Enregistrer");
  await settle(panel);
  input(panel, "name", "Second");
  resolveSave({
    ...fixture(),
    revision: 2,
    config: sent.config as Snapshot["config"],
  });
  await settle(panel);
  assert.equal(
    panel.shadowRoot!.querySelector<HTMLInputElement>("[data-field=name]")!
      .value,
    "Second",
  );
  assert.ok(panel.shadowRoot!.querySelector(".savebar"));
});
test("revision conflict preserves draft and prevents overwriting server", async () => {
  const { panel, emit, calls } = await mount();
  click(panel, "Personnes");
  await settle(panel);
  input(panel, "name", "Mine");
  await settle(panel);
  const changed = fixture();
  changed.revision = 2;
  changed.config.persons[0].name = "Theirs";
  emit(changed);
  await settle(panel);
  assert.match(panel.shadowRoot!.textContent!, /changé ailleurs/);
  assert.ok(
    buttons(panel).find(
      (button) => button.textContent?.trim() === "Enregistrer",
    )!.disabled,
  );
  click(panel, "Abandonner");
  await settle(panel);
  assert.equal(
    panel.shadowRoot!.querySelector<HTMLInputElement>("[data-field=name]")!
      .value,
    "Theirs",
  );
  assert.equal(calls.length, 0);
});
test("stale snapshots do not roll back saved data", async () => {
  const { panel, emit } = await mount();
  const latest = fixture();
  latest.revision = 3;
  latest.config.persons[0].name = "New";
  emit(latest);
  emit(fixture());
  click(panel, "Personnes");
  await settle(panel);
  assert.equal(
    panel.shadowRoot!.querySelector<HTMLInputElement>("[data-field=name]")!
      .value,
    "New",
  );
});
test("device choice auto-fills Companion platform and device ID", async () => {
  const { panel, calls } = await mount();
  click(panel, "Personnes");
  await settle(panel);
  click(panel, "Ajouter un appareil");
  await settle(panel);
  const service = [
    ...panel.shadowRoot!.querySelectorAll<HTMLSelectElement>("select"),
  ].find((select) =>
    select.querySelector('option[value="notify.mobile_app_alex"]'),
  )!;
  service.value = "notify.mobile_app_alex";
  service.dispatchEvent(new Event("change"));
  await settle(panel);
  assert.equal(
    panel.shadowRoot!.querySelector<HTMLInputElement>("[data-field=deviceId]")!
      .value,
    "device-a",
  );
  assert.equal(
    panel.shadowRoot!.querySelector<HTMLSelectElement>("[data-field=platform]")!
      .value,
    "ios",
  );
  click(panel, "Enregistrer");
  await settle(panel);
  assert.equal(
    (calls[0].config as Snapshot["config"]).persons[0].devices[0].target,
    "notify.mobile_app_alex",
  );
});
test("simulation and real test use distinct endpoints without profiles", async () => {
  const { panel, calls } = await mount();
  click(panel, "Tests et réglages");
  await settle(panel);
  input(panel, "message", "Hello");
  select(panel, "recipients", "all");
  await settle(panel);
  click(panel, "Simuler sans envoyer");
  await settle(panel);
  click(panel, "Envoyer un test réel");
  await settle(panel);
  assert.deepEqual(
    calls.map((call) => call.type),
    ["hano/preview", "hano/send"],
  );
  assert.equal((calls[0].request as Request).recipient_mode, "all");
  assert.equal((calls[0].request as Request).message, "Hello");
});
test("priority changes do not disable sleep", async () => {
  const { panel, calls } = await mount();
  click(panel, "Tests et réglages");
  await settle(panel);
  input(panel, "message", "Critical");
  select(panel, "priority", "critical");
  await settle(panel);
  click(panel, "Simuler sans envoyer");
  await settle(panel);
  assert.equal((calls[0].request as Request).respect_sleep, true);
  assert.equal((calls[0].request as Request).priority, "critical");
});
test("empty message cannot send", async () => {
  const { panel, calls } = await mount();
  click(panel, "Tests et réglages");
  await settle(panel);
  click(panel, "Envoyer un test réel");
  await settle(panel);
  assert.equal(calls.length, 0);
  assert.match(panel.shadowRoot!.textContent!, /Saisis un message/);
});
test("configuration draft disables preview and real send", async () => {
  const { panel } = await mount();
  click(panel, "Tests et réglages");
  await settle(panel);
  input(panel, "retention", "60");
  await settle(panel);
  assert.ok(
    buttons(panel).find(
      (button) => button.textContent?.trim() === "Envoyer un test réel",
    )!.disabled,
  );
  assert.ok(
    buttons(panel).find(
      (button) => button.textContent?.trim() === "Simuler sans envoyer",
    )!.disabled,
  );
});
test("resolution calls exact logical ID", async () => {
  const { panel, calls } = await mount();
  click(panel, "Laundry finishedwasherEn attente");
  await settle(panel);
  click(panel, "Résoudre partout");
  await settle(panel);
  assert.deepEqual(calls[0], {
    type: "hano/resolve",
    notification_id: "washer",
  });
});
test("purge has an explicit confirmation and ignores active notifications at API boundary", async () => {
  const { panel, calls } = await mount();
  click(panel, "Tests et réglages");
  await settle(panel);
  click(panel, "Purger l’historique terminé");
  await settle(panel);
  assert.equal(calls.length, 0);
  assert.match(panel.shadowRoot!.textContent!, /actives seront conservées/);
  click(panel, "Confirmer");
  await settle(panel);
  assert.deepEqual(calls[0], { type: "hano/purge_history" });
});
test("locale change preserves draft and custom names", async () => {
  const { panel, hass } = await mount();
  click(panel, "Personnes");
  await settle(panel);
  input(panel, "name", "My custom name");
  panel.hass = { ...hass, language: "es-MX" };
  await settle(panel);
  assert.match(panel.shadowRoot!.textContent!, /Personas/);
  assert.equal(
    panel.shadowRoot!.querySelector<HTMLInputElement>("[data-field=name]")!
      .value,
    "My custom name",
  );
  assert.equal(
    panel.shadowRoot!.querySelector("main")!.getAttribute("lang"),
    "es",
  );
});
test("menu event bubbles with open true and preserves draft", async () => {
  const { panel, calls } = await mount();
  panel.narrow = true;
  await settle(panel);
  click(panel, "Personnes");
  await settle(panel);
  input(panel, "name", "Still here");
  let detail: unknown;
  const listener = (event: Event) => {
    detail = (event as CustomEvent).detail;
  };
  document.body.addEventListener("hass-toggle-menu", listener);
  panel
    .shadowRoot!.querySelector<HTMLButtonElement>(".sidebar-toggle")!
    .click();
  document.body.removeEventListener("hass-toggle-menu", listener);
  assert.deepEqual(detail, { open: true });
  assert.equal(calls.length, 0);
  assert.equal(
    panel.shadowRoot!.querySelector<HTMLInputElement>("[data-field=name]")!
      .value,
    "Still here",
  );
});
test("menu is hidden on wide docked layout", async () => {
  const { panel } = await mount();
  assert.equal(panel.shadowRoot!.querySelector(".sidebar-toggle"), null);
});
test("URI button clears callback actions and resolution", async () => {
  const { panel, calls } = await mount();
  click(panel, "Tests et réglages");
  await settle(panel);
  input(panel, "message", "Hello");
  click(panel, "Ajouter un bouton");
  await settle(panel);
  input(panel, "buttonLabel", "Open");
  select(panel, "buttonKind", "uriButton");
  await settle(panel);
  const links =
    panel.shadowRoot!.querySelectorAll<HTMLInputElement>("[data-field=link]");
  const link = links[links.length - 1];
  link.value = "/lovelace";
  link.dispatchEvent(new Event("input"));
  await settle(panel);
  click(panel, "Simuler sans envoyer");
  await settle(panel);
  const button = (calls[0].request as Request).buttons[0];
  assert.equal(button.uri, "/lovelace");
  assert.deepEqual(button.actions, []);
  assert.equal(button.resolve, false);
});

test("history selects an exact cycle when a logical ID is reused", async () => {
  const { panel, emit } = await mount();
  const state = fixture();
  state.notifications.push({
    ...structuredClone(state.notifications[0]),
    cycle_id: "old-cycle",
    status: "resolved",
    title: "Previous cycle",
    message: "Old content",
  });
  emit(state);
  await settle(panel);
  click(panel, "Historique");
  await settle(panel);
  const row = panel.shadowRoot!.querySelector<HTMLButtonElement>(
    ".notification-list button",
  )!;
  row.click();
  await settle(panel);
  assert.match(
    panel.shadowRoot!.querySelector(".detail")!.textContent!,
    /Old content/,
  );
  assert.doesNotMatch(
    panel.shadowRoot!.querySelector(".detail")!.textContent!,
    /The laundry can be removed/,
  );
  assert.equal(
    buttons(panel).some(
      (button) => button.textContent?.trim() === "Résoudre partout",
    ),
    false,
  );
});
test("unsaved edits protect browser navigation and discard clears the protection", async () => {
  const { panel } = await mount();
  click(panel, "Personnes");
  await settle(panel);
  input(panel, "name", "Draft");
  await settle(panel);
  const pending = new window.Event("beforeunload", { cancelable: true });
  window.dispatchEvent(pending);
  assert.equal(pending.defaultPrevented, true);
  click(panel, "Abandonner");
  await settle(panel);
  const clean = new window.Event("beforeunload", { cancelable: true });
  window.dispatchEvent(clean);
  assert.equal(clean.defaultPrevented, false);
});
test("a newer server revision received during save becomes a conflict after acknowledgment", async () => {
  let resolveSave!: (value: Snapshot) => void;
  let sent!: Record<string, unknown>;
  const { panel, emit } = await mount({
    save: (message) => {
      sent = message;
      return new Promise((resolve) => (resolveSave = resolve));
    },
  });
  click(panel, "Personnes");
  await settle(panel);
  input(panel, "name", "Submitted");
  await settle(panel);
  click(panel, "Enregistrer");
  await settle(panel);
  input(panel, "name", "Later local edit");
  const newest = fixture();
  newest.revision = 3;
  newest.config.persons[0].name = "Another admin";
  emit(newest);
  resolveSave({
    ...fixture(),
    revision: 2,
    config: sent.config as Snapshot["config"],
  });
  await settle(panel);
  assert.match(panel.shadowRoot!.textContent!, /changé ailleurs/);
  assert.equal(
    panel.shadowRoot!.querySelector<HTMLInputElement>("[data-field=name]")!
      .value,
    "Later local edit",
  );
});
test("native action selector receives and returns the complete sequence", async () => {
  class NativeSelector extends HTMLElement {
    hass?: Hass;
    selector?: unknown;
    value?: unknown;
  }
  if (!customElements.get("ha-selector"))
    customElements.define("ha-selector", NativeSelector);
  const { panel, calls } = await mount();
  click(panel, "Tests et réglages");
  await settle(panel);
  input(panel, "message", "Actions test");
  click(panel, "Ajouter un bouton");
  await settle(panel);
  input(panel, "buttonLabel", "Finished");
  await settle(panel);
  const selector =
    panel.shadowRoot!.querySelector<NativeSelector>("ha-selector")!;
  assert.deepEqual(selector.selector, { action: {} });
  const sequence = [
    {
      action: "input_boolean.turn_on",
      target: { entity_id: "input_boolean.done" },
    },
  ];
  selector.dispatchEvent(
    new CustomEvent("value-changed", { detail: { value: sequence } }),
  );
  await settle(panel);
  click(panel, "Simuler sans envoyer");
  await settle(panel);
  assert.deepEqual((calls[0].request as Request).buttons[0].actions, sequence);
});
test("button IDs can be edited without replacing their focused input", async () => {
  const { panel } = await mount();
  click(panel, "Tests et réglages");
  await settle(panel);
  click(panel, "Ajouter un bouton");
  await settle(panel);
  const element = input(panel, "buttonId", "a");
  element.focus();
  await settle(panel);
  assert.equal(
    panel.shadowRoot!.querySelector("[data-field=buttonId]"),
    element,
  );
  input(panel, "buttonId", "acknowledge");
  await settle(panel);
  assert.equal(
    panel.shadowRoot!.querySelector("[data-field=buttonId]"),
    element,
  );
  assert.equal(element.value, "acknowledge");
});

test("rooms can be added and saved on HTTP without crypto.randomUUID", async (t) => {
  const original = Object.getOwnPropertyDescriptor(globalThis, "crypto")!;
  const getRandomValues = globalThis.crypto.getRandomValues.bind(globalThis.crypto);
  Object.defineProperty(globalThis, "crypto", {
    configurable: true,
    value: { getRandomValues },
  });
  t.after(() => Object.defineProperty(globalThis, "crypto", original));

  const { panel, calls } = await mount();
  click(panel, "Pièces et voix");
  await settle(panel);
  click(panel, "Ajouter une pièce");
  await settle(panel);
  click(panel, "Ajouter une pièce");
  await settle(panel);
  const names = panel.shadowRoot!.querySelectorAll<HTMLInputElement>(
    '[data-field="roomName"]',
  );
  names.forEach((element, index) => {
    element.value = `Room ${index + 1}`;
    element.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await settle(panel);
  click(panel, "Enregistrer");
  await settle(panel);

  const config = calls[0].config as Snapshot["config"];
  assert.equal(config.rooms.length, 2);
  const ids = config.rooms.map((room) => room.id);
  assert.equal(new Set(ids).size, 2);
  for (const id of ids)
    assert.match(
      id,
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
    );
});

test("buttons can be added and previewed on HTTP without crypto.randomUUID", async (t) => {
  const original = Object.getOwnPropertyDescriptor(globalThis, "crypto")!;
  const getRandomValues = globalThis.crypto.getRandomValues.bind(globalThis.crypto);
  Object.defineProperty(globalThis, "crypto", {
    configurable: true,
    value: { getRandomValues },
  });
  t.after(() => Object.defineProperty(globalThis, "crypto", original));

  const { panel, calls } = await mount();
  click(panel, "Tests et réglages");
  await settle(panel);
  input(panel, "message", "HTTP notification test");
  click(panel, "Ajouter un bouton");
  await settle(panel);
  input(panel, "buttonLabel", "Finished");
  click(panel, "Simuler sans envoyer");
  await settle(panel);

  assert.equal(calls[0].type, "hano/preview");
  const buttons = (calls[0].request as Request).buttons;
  assert.equal(buttons.length, 1);
  assert.match(buttons[0].id, /^button_[0-9a-f]{8}$/);
  assert.equal(buttons[0].label, "Finished");
});
