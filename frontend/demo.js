import "../custom_components/hano/frontend/hano-panel.js";
const params = new URLSearchParams(location.search);
let language = params.get("lang") || "en",
  dark = params.get("theme") === "dark";
const localized = {
  en: {
    demo: "Local demonstration · simulated calls only",
    theme: "Theme",
    reset: "Reset",
    menu: "Home Assistant menu requested",
    alex: "Alex",
    sam: "Sam",
    sleep: "Alex sleeping",
    room: "Living room",
    occupied: "Living room occupied",
    silent: "Living room quiet",
    speaker: "Living room speaker",
    title: "Laundry finished",
    message:
      "The laundry can be removed. Resolve the notification when you have taken care of it.",
    history: "Front door checked",
    historyMessage: "The front door is now closed.",
  },
  fr: {
    demo: "Démonstration locale · appels simulés uniquement",
    theme: "Thème",
    reset: "Réinitialiser",
    menu: "Ouverture du menu Home Assistant demandée",
    alex: "Alex",
    sam: "Sam",
    sleep: "Alex endormi",
    room: "Salon",
    occupied: "Salon occupé",
    silent: "Salon silencieux",
    speaker: "Enceinte du salon",
    title: "Machine terminée",
    message:
      "Le linge peut être retiré. Résous la notification lorsque tu t’en es occupé.",
    history: "Porte d’entrée vérifiée",
    historyMessage: "La porte d’entrée est maintenant fermée.",
  },
  es: {
    demo: "Demostración local · solo llamadas simuladas",
    theme: "Tema",
    reset: "Restablecer",
    menu: "Se solicitó abrir el menú de Home Assistant",
    alex: "Alex",
    sam: "Sam",
    sleep: "Alex dormido",
    room: "Salón",
    occupied: "Salón ocupado",
    silent: "Salón en silencio",
    speaker: "Altavoz del salón",
    title: "Lavadora terminada",
    message:
      "Ya puedes sacar la ropa. Resuelve la notificación cuando te hayas ocupado de ella.",
    history: "Puerta de entrada comprobada",
    historyMessage: "La puerta de entrada está cerrada.",
  },
};
const baseLanguage = () =>
  language.startsWith("fr") ? "fr" : language.startsWith("es") ? "es" : "en";
let strings = localized[baseLanguage()];
const request = {
  notification_id: "laundry_finished",
  title: "",
  message: "",
  recipient_mode: "present",
  person_entity_ids: [],
  notify_entity_ids: [],
  mobile_device_ids: [],
  channels: ["mobile", "persistent"],
  respect_sleep: true,
  delivery: "when_available",
  priority: "normal",
  cycle_mode: "update",
  expires_in: 0,
  resolve_on_clear: false,
  image_url: "",
  click_url: "",
  camera_entity_id: "",
  icon: "",
  color: "",
  timeout: 0,
  voice_mode: "explicit",
  media_player_entity_ids: [],
  tts_entity_id: "",
  tts_language: "",
  voice_message: "",
  volume: null,
  buttons: [],
};
const makeSnapshot = () => {
  const time = "2026-10-21T14:32:00Z";
  return {
    version: "0.1.0b1",
    revision: 1,
    config: {
      persons: [
        {
          person_id: "person.sam",
          name: "Sam",
          sleep_entity_id: "",
          devices: [
            {
              type: "mobile",
              target: "notify.mobile_app_sam",
              platform: "android",
              device_id: "demo_sam",
            },
          ],
        },
        {
          person_id: "person.alex",
          name: "Alex",
          sleep_entity_id: "binary_sensor.alex_sleeping",
          devices: [
            {
              type: "mobile",
              target: "notify.mobile_app_alex",
              platform: "ios",
              device_id: "demo_alex",
            },
          ],
        },
      ],
      rooms: [
        {
          id: "living_room",
          name: strings.room,
          presence_entity_id: "binary_sensor.living_room_occupied",
          sleep_entity_id: "input_boolean.living_room_quiet",
          media_player_entity_ids: ["media_player.living_room"],
        },
      ],
      tts_entity_id: "tts.local",
      tts_language: baseLanguage(),
      history_days: 30,
      native_volume_entity_ids: [],
    },
    notifications: [
      {
        notification_id: "laundry_finished",
        cycle_id: "demo-cycle-laundry",
        status: "active",
        title: strings.title,
        message: strings.message,
        created_at: time,
        updated_at: time,
        resolved_at: null,
        expires_at: null,
        request: { ...request, title: strings.title, message: strings.message },
        deliveries: [
          {
            key: "sam",
            person_id: "person.sam",
            channel: "mobile",
            target: "notify.mobile_app_sam",
            status: "accepted",
            reason: "eligible",
            updated_at: time,
          },
          {
            key: "alex",
            person_id: "person.alex",
            channel: "mobile",
            target: "notify.mobile_app_alex",
            status: "pending",
            reason: "sleeping",
            updated_at: time,
          },
          {
            key: "ha",
            person_id: "",
            channel: "persistent",
            target: "persistent_notification",
            status: "accepted",
            reason: "eligible",
            updated_at: time,
          },
        ],
        history: [
          { at: time, event: "created" },
          { at: time, event: "accepted", target: "notify.mobile_app_sam" },
          {
            at: time,
            event: "pending",
            target: "notify.mobile_app_alex",
            detail: "sleeping",
          },
        ],
      },
      {
        notification_id: "front_door",
        cycle_id: "demo-cycle-door",
        status: "resolved",
        title: strings.history,
        message: strings.historyMessage,
        created_at: "2026-10-21T09:04:00Z",
        updated_at: "2026-10-21T09:07:00Z",
        resolved_at: "2026-10-21T09:07:00Z",
        expires_at: null,
        request,
        deliveries: [],
        history: [{ at: "2026-10-21T09:07:00Z", event: "resolved" }],
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
          entity_id: "person.sam",
          name: "Sam",
          domain: "person",
          state: "home",
        },
        {
          entity_id: "binary_sensor.alex_sleeping",
          name: strings.sleep,
          domain: "binary_sensor",
          state: "on",
        },
        {
          entity_id: "binary_sensor.living_room_occupied",
          name: strings.occupied,
          domain: "binary_sensor",
          state: "on",
        },
        {
          entity_id: "input_boolean.living_room_quiet",
          name: strings.silent,
          domain: "input_boolean",
          state: "off",
        },
        {
          entity_id: "media_player.living_room",
          name: strings.speaker,
          domain: "media_player",
          state: "idle",
        },
        {
          entity_id: "tts.local",
          name: "Piper",
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
      areas: [{ area_id: "living_room", name: strings.room }],
      mobile_services: [
        {
          service: "notify.mobile_app_alex",
          name: "Alex · iPhone",
          platform: "ios",
          device_id: "demo_alex",
        },
        {
          service: "notify.mobile_app_sam",
          name: "Sam · Android",
          platform: "android",
          device_id: "demo_sam",
        },
      ],
      mobile_devices: [
        {
          service: "notify.mobile_app_alex",
          name: "Alex · iPhone",
          platform: "ios",
          device_id: "demo_alex",
        },
        {
          service: "notify.mobile_app_sam",
          name: "Sam · Android",
          platform: "android",
          device_id: "demo_sam",
        },
      ],
    },
  };
};
let snapshot = makeSnapshot(),
  emit = () => {};
const panel = document.querySelector("hano-panel");
const connection = {
  async subscribeMessage(callback) {
    emit = callback;
    callback(structuredClone(snapshot));
    return () => {
      emit = () => {};
    };
  },
};
const hass = {
  user: { is_admin: true },
  language,
  connection,
  themes: { darkMode: dark },
  async callWS(message) {
    await new Promise((resolve) => setTimeout(resolve, 160));
    if (message.type === "hano/save") {
      if (message.revision !== snapshot.revision) throw { code: "conflict" };
      snapshot = {
        ...snapshot,
        revision: snapshot.revision + 1,
        config: structuredClone(message.config),
      };
      emit(structuredClone(snapshot));
      return structuredClone(snapshot);
    }
    if (message.type === "hano/resolve") {
      const record = snapshot.notifications.find(
        (item) => item.notification_id === message.notification_id,
      );
      if (record) {
        record.status = "resolved";
        record.resolved_at = new Date().toISOString();
        record.deliveries.forEach(
          (delivery) =>
            (delivery.status =
              delivery.status === "pending" ? "cancelled" : "clear_requested"),
        );
        record.history.push({ at: record.resolved_at, event: "resolved" });
      }
      emit(structuredClone(snapshot));
      return { notification_id: message.notification_id, status: "resolved" };
    }
    if (message.type === "hano/purge_history") {
      snapshot.notifications = snapshot.notifications.filter(
        (record) => record.status === "active",
      );
      emit(structuredClone(snapshot));
      return { purged: true };
    }
    const routing = {
      persons: snapshot.config.persons
        .filter(
          (person) =>
            message.request.recipient_mode !== "selected" ||
            message.request.person_entity_ids.includes(person.person_id),
        )
        .map((person) => ({
          person_id: person.person_id,
          eligible: !message.request.respect_sleep || !person.sleep_entity_id,
          reason:
            message.request.respect_sleep && person.sleep_entity_id
              ? "sleeping"
              : "eligible",
        })),
      media_player_entity_ids: message.request.media_player_entity_ids,
      reasons: [],
    };
    if (message.type === "hano/preview") return routing;
    if (message.type === "hano/send") {
      const now = new Date().toISOString();
      const id = message.request.notification_id || `demo_${Date.now()}`;
      const record = {
        notification_id: id,
        cycle_id: `demo_cycle_${Date.now()}`,
        status: "active",
        title: message.request.title,
        message: message.request.message,
        created_at: now,
        updated_at: now,
        resolved_at: null,
        expires_at: null,
        request: message.request,
        deliveries: routing.persons.map((person) => ({
          key: person.person_id,
          person_id: person.person_id,
          channel: "mobile",
          target: person.person_id,
          status: person.eligible
            ? "accepted"
            : message.request.delivery === "when_available"
              ? "pending"
              : "skipped",
          reason: person.reason,
          updated_at: now,
        })),
        history: [{ at: now, event: "created" }],
      };
      snapshot.notifications = [
        record,
        ...snapshot.notifications.filter((item) => item.notification_id !== id),
      ];
      emit(structuredClone(snapshot));
      return {
        notification_id: id,
        cycle_id: record.cycle_id,
        deliveries: record.deliveries,
      };
    }
    return {};
  },
};
function update() {
  strings = localized[baseLanguage()];
  document.documentElement.lang = baseLanguage();
  document.querySelector("#demo-label").textContent = strings.demo;
  document.querySelector("#theme").textContent = strings.theme;
  document.querySelector("#reset").textContent = strings.reset;
  document.querySelector("#language").value = baseLanguage();
  document.documentElement.style.cssText = dark
    ? "--primary-background-color:#111;--ha-card-background:#1c1c1c;--primary-text-color:#e1e1e1;--secondary-text-color:#a0a0a0;--divider-color:#353535;--primary-color:#03a9f4;--text-primary-color:#fff;--app-header-background-color:#1c1c1c;--app-header-text-color:#e1e1e1;color-scheme:dark"
    : "";
  panel.hass = { ...hass, language, themes: { darkMode: dark } };
  panel.narrow = innerWidth <= 870;
}
window.addEventListener("resize", update);
document.querySelector("#theme").onclick = () => {
  dark = !dark;
  update();
};
document.querySelector("#language").onchange = (event) => {
  language = event.target.value;
  update();
};
document.querySelector("#reset").onclick = () => {
  snapshot = makeSnapshot();
  emit(structuredClone(snapshot));
  location.reload();
};
document.body.addEventListener("hass-toggle-menu", () => {
  const toast = document.createElement("div");
  toast.className = "menu-toast";
  toast.textContent = strings.menu;
  document.body.append(toast);
  setTimeout(() => toast.remove(), 2000);
});
if (params.get("clean") === "1") document.body.classList.add("demo-hide");
update();
