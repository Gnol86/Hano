import {
  LitElement,
  html,
  nothing,
  type PropertyValues,
  type TemplateResult,
} from "lit";
import { repeat } from "lit/directives/repeat.js";
import { Draft, copy, emptyRequest, errorCode, toggle } from "./model";
import { createId } from "./id";
import {
  translate,
  translateKnown,
  resolveLanguage,
  en,
  type TranslationKey,
} from "./translations";
import { styles } from "./styles";
import type {
  Button,
  Config,
  Device,
  Hass,
  Notification,
  Person,
  Request,
  Room,
  Snapshot,
} from "./types";

type Page = "notifications" | "people" | "rooms" | "settings";
export class HanoPanel extends LitElement {
  static properties = {
    hass: { attribute: false },
    narrow: { type: Boolean },
    snapshot: { state: true },
    page: { state: true },
    selected: { state: true },
    filter: { state: true },
    query: { state: true },
    error: { state: true },
    message: { state: true },
    saving: { state: true },
    busy: { state: true },
    request: { state: true },
    result: { state: true },
    purging: { state: true },
    revisionTick: { state: true },
  };
  static styles = styles;
  hass?: Hass;
  narrow = false;
  private snapshot?: Snapshot;
  private draft = new Draft();
  private page: Page = "notifications";
  private selected = "";
  private filter = "active";
  private query = "";
  private error = "";
  private message = "";
  private saving = false;
  private busy = false;
  private request = emptyRequest();
  private result: Record<string, unknown> | null = null;
  private purging = false;
  private revisionTick = 0;
  private connection?: Hass["connection"];
  private unsubscribe?: () => void;
  private generation = 0;
  private admin = false;
  private resultKind: "previewOutcome" | "sendOutcome" = "previewOutcome";
  private beforeUnload = (event: BeforeUnloadEvent) => {
    if (this.draft.dirty) {
      event.preventDefault();
      event.returnValue = "";
    }
  };
  connectedCallback() {
    super.connectedCallback();
    window.addEventListener("beforeunload", this.beforeUnload);
    if (this.hass) void this.connect();
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    ++this.generation;
    this.unsubscribe?.();
    this.unsubscribe = undefined;
    this.connection = undefined;
    window.removeEventListener("beforeunload", this.beforeUnload);
  }
  protected updated(changed: PropertyValues) {
    if (changed.has("hass")) {
      this.style.colorScheme = this.hass?.themes?.darkMode ? "dark" : "light";
      if (this.hass?.user?.is_admin === false) {
        this.revoke();
        return;
      }
      if (this.hass?.connection !== this.connection) void this.connect();
    }
  }
  private revoke() {
    ++this.generation;
    this.unsubscribe?.();
    this.unsubscribe = undefined;
    this.connection = undefined;
    this.snapshot = undefined;
    this.draft = new Draft();
    this.request = emptyRequest();
    this.result = null;
    this.admin = false;
    this.error = "forbidden";
    this.message = "";
  }
  private get locale() {
    return this.hass?.locale?.language ?? this.hass?.language;
  }
  private t(key: TranslationKey) {
    return translate(key, this.locale);
  }
  private text(key: string) {
    return translateKnown(key, this.locale);
  }
  private get config() {
    return this.draft.value;
  }
  private get canAct() {
    return (
      this.admin &&
      !this.busy &&
      !this.saving &&
      !this.draft.dirty &&
      !this.draft.conflict
    );
  }
  private async connect() {
    if (!this.hass || !this.isConnected) return;
    if (this.hass.user?.is_admin === false) {
      this.revoke();
      return;
    }
    const generation = ++this.generation;
    this.unsubscribe?.();
    this.connection = this.hass.connection;
    this.error = "";
    try {
      const unsub = await this.connection.subscribeMessage<Snapshot>(
        (snapshot) => {
          if (generation === this.generation) {
            this.admin = true;
            this.receive(snapshot);
          }
        },
        { type: "hano/subscribe" },
      );
      if (generation !== this.generation) unsub();
      else this.unsubscribe = unsub;
    } catch (error) {
      if (generation === this.generation) this.fail(error);
    }
  }
  private receive(snapshot: Snapshot) {
    if (this.snapshot && snapshot.revision < this.snapshot.revision) return;
    this.snapshot = snapshot;
    if (!this.saving) this.draft.receive(snapshot.config, snapshot.revision);
    this.requestUpdate();
  }
  private fail(error: unknown) {
    const code = errorCode(error);
    if (["unauthorized", "forbidden"].includes(code)) {
      this.revoke();
      return;
    }
    this.error = code in en ? code : "error";
    if (["revision_conflict", "conflict"].includes(code))
      this.draft.conflict = true;
  }
  private touch() {
    this.revisionTick++;
    this.message = "";
    this.requestUpdate();
  }
  private valid() {
    const input = [
      ...this.renderRoot.querySelectorAll<HTMLInputElement>(
        "input,textarea,select",
      ),
    ].find((item) => !item.validity.valid);
    if (input) {
      input.reportValidity();
      input.focus();
      return false;
    }
    return true;
  }
  private async save() {
    if (!this.admin || this.saving || this.draft.conflict || !this.valid())
      return;
    const sent = copy(this.config);
    const generation = this.generation;
    this.saving = true;
    this.error = "";
    try {
      const result = await this.hass!.callWS<Snapshot>({
        type: "hano/save",
        config: sent,
        revision: this.draft.revision,
      });
      if (generation !== this.generation) return;
      this.draft.acknowledge(sent, result.config, result.revision);
      this.receive(result);
      this.message = "saved";
    } catch (error) {
      if (generation === this.generation) this.fail(error);
    } finally {
      this.saving = false;
      if (this.snapshot && this.snapshot.revision > this.draft.revision)
        this.draft.receive(this.snapshot.config, this.snapshot.revision);
      this.requestUpdate();
    }
  }
  private discard() {
    if (this.snapshot)
      this.draft.reset(this.snapshot.config, this.snapshot.revision);
    this.error = "";
    this.message = "";
    this.touch();
  }
  private async action(type: string, data: Record<string, unknown> = {}) {
    if (!this.canAct) return;
    this.busy = true;
    this.error = "";
    this.message = "";
    const generation = this.generation;
    try {
      const result = await this.hass!.callWS<Record<string, unknown>>({
        type,
        ...data,
      });
      if (generation !== this.generation) return;
      if (type === "hano/preview" || type === "hano/send") {
        this.result = result;
        this.resultKind =
          type === "hano/preview" ? "previewOutcome" : "sendOutcome";
      } else if (type === "hano/purge_history") {
        this.purging = false;
        this.message = "purged";
      } else this.message = "resolved";
    } catch (error) {
      if (generation === this.generation) this.fail(error);
    } finally {
      this.busy = false;
    }
  }
  private test(send: boolean) {
    if (!this.request.message.trim()) {
      this.error = "emptyMessage";
      return;
    }
    if (!this.valid()) return;
    void this.action(send ? "hano/send" : "hano/preview", {
      request: copy(this.request),
    });
  }
  private editRequest<K extends keyof Request>(key: K, value: Request[K]) {
    this.request = { ...this.request, [key]: value };
    this.result = null;
  }
  private field(
    label: TranslationKey,
    value: string | number,
    change: (value: string) => void,
    type = "text",
    options: {
      required?: boolean;
      min?: number;
      max?: number;
      step?: string;
    } = {},
  ) {
    return html`<label
      >${this.t(label)}<input
        data-field=${label}
        .value=${String(value)}
        type=${type}
        ?required=${options.required}
        min=${options.min ?? nothing}
        max=${options.max ?? nothing}
        step=${options.step ?? nothing}
        @input=${(event: Event) => change((event.target as HTMLInputElement).value)}
    /></label>`;
  }
  private check(
    label: TranslationKey,
    value: boolean,
    change: (value: boolean) => void,
  ) {
    return html`<label class="check"
      ><input
        data-field=${label}
        type="checkbox"
        .checked=${value}
        @change=${(event: Event) => change((event.target as HTMLInputElement).checked)}
      />${this.t(label)}</label
    >`;
  }
  private select(
    label: TranslationKey,
    value: string,
    values: string[],
    change: (value: string) => void,
  ) {
    return html`<label
      >${this.t(label)}<select
        data-field=${label}
        .value=${value}
        @change=${(event: Event) => change((event.target as HTMLSelectElement).value)}
      >
        ${values.map((option) => html`<option value=${option} .selected=${option === value}>${this.text(option)}</option>`)}
      </select></label
    >`;
  }
  private entity(
    label: TranslationKey,
    value: string,
    domains: string[],
    change: (value: string) => void,
    required = false,
  ) {
    const entities =
      this.snapshot?.catalog.entities.filter((entity) =>
        domains.includes(entity.domain),
      ) ?? [];
    const native = customElements.get("ha-entity-picker");
    if (native)
      return html`<div class="field">
        <ha-entity-picker
          .hass=${this.hass}
          .label=${this.t(label)}
          .value=${value || undefined}
          .includeDomains=${domains}
          .allowCustomEntity=${false}
          .required=${required}
          @value-changed=${(event: CustomEvent) => change(event.detail.value ?? "")}
        ></ha-entity-picker>
      </div>`;
    return html`<label
      >${this.t(label)}<select
        data-field=${label}
        .value=${value}
        ?required=${required}
        @change=${(event: Event) => change((event.target as HTMLSelectElement).value)}
      >
        <option value="" .selected=${!value}>
          ${this.t(required ? "select" : "none")}
        </option>
        ${value && !entities.some((entity) => entity.entity_id === value) ? html`<option value=${value} selected>${value} · ${this.t("unavailable")}</option>` : nothing}${entities.map((entity) => html`<option value=${entity.entity_id} .selected=${value === entity.entity_id}>${entity.name} (${entity.entity_id})</option>`)}
      </select></label
    >`;
  }
  private choices(
    label: TranslationKey,
    values: string[],
    options: { id: string; name: string }[],
    change: (values: string[]) => void,
  ) {
    const merged = [
      ...options,
      ...values
        .filter((value) => !options.some((option) => option.id === value))
        .map((id) => ({ id, name: `${id} · ${this.t("unavailable")}` })),
    ];
    return html`<fieldset>
      <legend>${this.t(label)}</legend>
      <div class="choices">
        ${merged.length ? merged.map((option) => html`<label class="check"><input type="checkbox" .checked=${values.includes(option.id)} @change=${() => change(toggle(values, option.id))} />${option.name}</label>`) : html`<small>${this.t("noEntities")}</small>`}
      </div>
    </fieldset>`;
  }
  private entities(domains: string[]) {
    return (
      this.snapshot?.catalog.entities
        .filter((entity) => domains.includes(entity.domain))
        .map((entity) => ({ id: entity.entity_id, name: entity.name })) ?? []
    );
  }
  private date(value: string | null) {
    if (!value) return this.t("unlimited");
    const date = new Date(value);
    return Number.isNaN(date.valueOf())
      ? value
      : new Intl.DateTimeFormat(this.locale ?? "en", {
          dateStyle: "medium",
          timeStyle: "short",
        }).format(date);
  }
  private personName(id: string) {
    return (
      this.config.persons.find((person) => person.person_id === id)?.name ||
      this.snapshot?.catalog.entities.find((entity) => entity.entity_id === id)
        ?.name ||
      id
    );
  }
  private notificationView() {
    const notifications = (this.snapshot?.notifications ?? []).filter(
      (record) =>
        (this.filter === "history"
          ? record.status !== "active"
          : record.status === "active") &&
        (this.filter !== "pending" ||
          record.deliveries.some(
            (delivery) => delivery.status === "pending",
          )) &&
        `${record.title} ${record.message} ${record.notification_id}`
          .toLocaleLowerCase()
          .includes(this.query.toLocaleLowerCase()),
    );
    const current = this.snapshot?.notifications.find(
      (record) => record.cycle_id === this.selected,
    );
    return html`<div class="workspace ${current ? "has-detail" : ""}">
      <aside class="rail">
        <h2>${this.t("notifications")}</h2>
        <label class="sr-only" for="search">${this.t("search")}</label
        ><input
          id="search"
          type="search"
          .value=${this.query}
          placeholder=${this.t("search")}
          @input=${(event: Event) => (this.query = (event.target as HTMLInputElement).value)}
        />
        <div class="filters">
          ${["active", "pending", "history"].map(
            (filter) =>
              html`<button
                aria-pressed=${String(this.filter === filter)}
                @click=${() => {
                  this.filter = filter;
                  this.selected = "";
                }}
              >
                ${this.text(filter)}
              </button>`,
          )}
        </div>
        ${
          notifications.length
            ? html`<ul class="notification-list">
                ${notifications.map(
                  (record) =>
                    html`<li>
                      <button
                        aria-pressed=${String(this.selected === record.cycle_id)}
                        @click=${() => (this.selected = record.cycle_id)}
                      >
                        <strong
                          >${record.title || record.notification_id}</strong
                        ><small>${record.notification_id}</small
                        ><span
                          class="badge ${record.deliveries.some((item) => item.status === "pending") ? "pending" : record.status}"
                          >${this.text(record.deliveries.some((item) => item.status === "pending") && record.status === "active" ? "pending" : record.status)}</span
                        >
                      </button>
                    </li>`,
                )}
              </ul>`
            : html`<p class="help">${this.t("noNotifications")}</p>`
        }
      </aside>
      <article class="detail">
        ${
          current
            ? this.notificationDetail(current)
            : html`<div class="empty">
                <h2>${this.t("chooseNotification")}</h2>
                <p>${this.t("chooseHint")}</p>
              </div>`
        }
      </article>
    </div>`;
  }
  private notificationDetail(record: Notification) {
    return html`<button class="back" @click=${() => (this.selected = "")}>
        ← ${this.t("back")}
      </button>
      <div class="section-heading">
        <div>
          <h2>${record.title || record.notification_id}</h2>
          <small
            >${record.notification_id} ·
            ${this.text(record.status === "active" ? "activeSingle" : record.status)}</small
          >
        </div>
        ${record.status === "active" ? html`<button class="primary" ?disabled=${!this.canAct} @click=${() => void this.action("hano/resolve", { notification_id: record.notification_id })}>${this.t("resolve")}</button>` : nothing}
      </div>
      <p class="body">${record.message}</p>
      <dl class="metadata">
        ${(
          [
            ["created", record.created_at],
            ["updated", record.updated_at],
            ["expires", record.expires_at],
          ] as const
        ).map(
          ([key, value]) =>
            html`<div>
              <dt>${this.t(key)}</dt>
              <dd>${this.date(value)}</dd>
            </div>`,
        )}
        <div>
          <dt>${this.t("cycle")}</dt>
          <dd><code>${record.cycle_id}</code></dd>
        </div>
      </dl>
      <section class="section">
        <h3>${this.t("deliveries")}</h3>
        <p class="help">${this.t("evidence")}</p>
        ${record.deliveries.map(
          (delivery) =>
            html`<div class="delivery">
              <div class="row">
                <strong
                  >${delivery.person_id ? this.personName(delivery.person_id) : this.text(delivery.channel)}</strong
                ><span class="badge ${delivery.status}"
                  >${this.text(delivery.status)}</span
                >
              </div>
              <small>${delivery.target}</small
              >${delivery.reason ? html`<div class="help">${this.text(delivery.reason)}</div>` : nothing}
              ${record.request.reminder_interval && delivery.channel === "mobile" ? html`<div class="help">${this.t("reminderCount")}: ${delivery.reminder_count ?? 0} / ${record.request.reminder_limit}${delivery.next_reminder_at ? html` · ${this.t("nextReminder")}: ${this.date(delivery.next_reminder_at)}` : nothing}</div>` : nothing}
            </div>`,
        )}
      </section>
      <section class="section">
        <h3>${this.t("timeline")}</h3>
        <ul class="timeline">
          ${record.history.map(
            (item) =>
              html`<li>
                <small>${this.date(item.at)}</small>
                <div>${this.text(item.event)}</div>
                ${item.target ? html`<div><small>${item.target}</small></div>` : nothing}${typeof item.detail === "string" && item.detail ? html`<div><small>${this.text(item.detail)}</small></div>` : nothing}
              </li>`,
          )}
        </ul>
      </section>`;
  }
  private peopleView() {
    return html`<div class="page">
      <section>
        <div class="section-heading">
          <h2>${this.t("people")}</h2>
          <button
            @click=${() => {
              this.config.persons.push({
                person_id: "",
                name: "",
                sleep_entity_id: "",
                devices: [],
              });
              this.touch();
            }}
          >
            ${this.t("addPerson")}
          </button>
        </div>
        <p class="help">
          ${this.t(this.config.persons.length ? "devicesHelp" : "noPeople")}
        </p>
        ${repeat(
          this.config.persons,
          (person) => person,
          (person) => this.personEditor(person),
        )}
      </section>
    </div>`;
  }
  private personEditor(person: Person) {
    const edit = (
      key: "person_id" | "name" | "sleep_entity_id",
      value: string,
    ) => {
      person[key] = value;
      this.touch();
    };
    return html`<section class="section">
      <div class="section-heading">
        <h3>
          ${person.name || this.personName(person.person_id) || this.t("person")}
        </h3>
        <button
          class="danger"
          aria-label=${this.t("removePerson")}
          @click=${() => {
            this.config.persons = this.config.persons.filter(
              (item) => item !== person,
            );
            this.touch();
          }}
        >
          ${this.t("remove")}
        </button>
      </div>
      <div class="grid">
        ${this.entity("person", person.person_id, ["person"], (value) => edit("person_id", value), true)}${this.field("name", person.name, (value) => edit("name", value))}${this.entity("sleep", person.sleep_entity_id, ["binary_sensor", "input_boolean"], (value) => edit("sleep_entity_id", value))}
      </div>
      <h3>${this.t("devices")}</h3>
      ${repeat(
        person.devices,
        (device) => device,
        (device) => this.deviceEditor(person, device),
      )}<button
        @click=${() => {
          person.devices.push({
            type: "mobile",
            target: "",
            platform: "generic",
            device_id: "",
          });
          this.touch();
        }}
      >
        ${this.t("addDevice")}
      </button>
    </section>`;
  }
  private deviceEditor(person: Person, device: Device) {
    const services = this.snapshot?.catalog.mobile_services ?? [];
    return html`<div class="device">
      <div class="grid">
        ${this.select("type", device.type, ["mobile", "notify"], (value) => {
          device.type = value as Device["type"];
          device.target = "";
          device.device_id = "";
          device.platform = "generic";
          this.touch();
        })}${
          device.type === "mobile"
            ? html`<label
                >${this.t("target")}<select
                  .value=${device.target}
                  required
                  @change=${(event: Event) => {
                    const target = (event.target as HTMLSelectElement).value;
                    const service = services.find(
                      (item) => item.service === target,
                    );
                    device.target = target;
                    device.device_id = service?.device_id ?? "";
                    device.platform = service?.platform ?? "generic";
                    this.touch();
                  }}
                >
                  <option value="">${this.t("select")}</option>
                  ${device.target && !services.some((service) => service.service === device.target) ? html`<option value=${device.target}>${device.target} · ${this.t("unavailable")}</option>` : nothing}${services.map((service) => html`<option value=${service.service} .selected=${device.target === service.service}>${service.name}</option>`)}
                </select></label
              >`
            : this.entity(
                "target",
                device.target,
                ["notify"],
                (value) => {
                  device.target = value;
                  this.touch();
                },
                true,
              )
        }${
          device.type === "mobile"
            ? html`${this.select(
                "platform",
                device.platform,
                ["ios", "android", "generic"],
                (value) => {
                  device.platform = value as Device["platform"];
                  this.touch();
                },
              )}${this.field("deviceId", device.device_id, (value) => {
                device.device_id = value;
                this.touch();
              })}`
            : nothing
        }
      </div>
      <button
        class="danger"
        @click=${() => {
          person.devices = person.devices.filter((item) => item !== device);
          this.touch();
        }}
      >
        ${this.t("remove")}
      </button>
    </div>`;
  }
  private roomsView() {
    return html`<div class="page">
      <section>
        <div class="section-heading">
          <h2>${this.t("rooms")}</h2>
          <button
            @click=${() => {
              this.config.rooms.push({
                id: createId(),
                name: "",
                presence_entity_id: "",
                sleep_entity_id: "",
                media_player_entity_ids: [],
              });
              this.touch();
            }}
          >
            ${this.t("addRoom")}
          </button>
        </div>
        <p class="help">${this.t("voiceHelp")}</p>
        ${!this.config.rooms.length ? html`<p class="help">${this.t("noRooms")}</p>` : nothing}${repeat(
          this.config.rooms,
          (room) => room,
          (room) => this.roomEditor(room),
        )}
      </section>
    </div>`;
  }
  private roomEditor(room: Room) {
    return html`<section class="section">
      <div class="section-heading">
        <h3>${room.name || this.t("roomName")}</h3>
        <button
          class="danger"
          aria-label=${this.t("removeRoom")}
          @click=${() => {
            this.config.rooms = this.config.rooms.filter(
              (item) => item !== room,
            );
            this.touch();
          }}
        >
          ${this.t("remove")}
        </button>
      </div>
      <div class="grid">
        ${this.field(
          "roomName",
          room.name,
          (value) => {
            room.name = value;
            this.touch();
          },
          "text",
          { required: true },
        )}<label
          >${this.t("area")}<select
            .value=${room.id}
            @change=${(event: Event) => {
              room.id = (event.target as HTMLSelectElement).value;
              const area = this.snapshot?.catalog.areas.find(
                (item) => item.area_id === room.id,
              );
              if (area && !room.name) room.name = area.name;
              this.touch();
            }}
          >
            ${!this.snapshot?.catalog.areas.some((area) => area.area_id === room.id) ? html`<option value=${room.id}>${room.name || this.t("none")}</option>` : nothing}${this.snapshot?.catalog.areas.map((area) => html`<option value=${area.area_id} .selected=${room.id === area.area_id}>${area.name}</option>`)}
          </select></label
        >${this.entity(
          "occupancy",
          room.presence_entity_id,
          ["binary_sensor", "input_boolean"],
          (value) => {
            room.presence_entity_id = value;
            this.touch();
          },
        )}${this.entity(
          "roomSleep",
          room.sleep_entity_id,
          ["binary_sensor", "input_boolean"],
          (value) => {
            room.sleep_entity_id = value;
            this.touch();
          },
        )}
      </div>
      ${this.choices(
        "speakers",
        room.media_player_entity_ids,
        this.entities(["media_player"]),
        (values) => {
          room.media_player_entity_ids = values;
          this.touch();
        },
      )}
    </section>`;
  }
  private settingsView() {
    return html`<div class="page">
      <h2>${this.t("settings")}</h2>
      <section class="section">
        <h3>${this.t("defaults")}</h3>
        <div class="grid">
          ${this.entity("tts", this.config.tts_entity_id, ["tts"], (value) => {
            this.config.tts_entity_id = value;
            this.touch();
          })}${this.field("language", this.config.tts_language, (value) => {
            this.config.tts_language = value;
            this.touch();
          })}
        </div>
        <details>
          <summary>${this.t("nativeVolume")}</summary>
          <p class="help">${this.t("nativeVolumeHelp")}</p>
          ${this.choices(
            "speakers",
            this.config.native_volume_entity_ids,
            this.entities(["media_player"]),
            (values) => {
              this.config.native_volume_entity_ids = values;
              this.touch();
            },
          )}
        </details>
      </section>
      <section class="section">
        <h3>${this.t("privacy")}</h3>
        <p class="help">${this.t("privacyHelp")}</p>
        ${this.field(
          "retention",
          this.config.history_days,
          (value) => {
            this.config.history_days = Number(value);
            this.touch();
          },
          "number",
          { required: true, min: 1, max: 3650, step: "1" },
        )}${
          this.purging
            ? html`<div class="confirm">
                <p>${this.t("confirmPurge")}</p>
                <div class="actions">
                  <button @click=${() => (this.purging = false)}>
                    ${this.t("cancel")}</button
                  ><button
                    class="danger"
                    ?disabled=${!this.canAct}
                    @click=${() => void this.action("hano/purge_history")}
                  >
                    ${this.t("confirm")}
                  </button>
                </div>
              </div>`
            : html`<button
                class="danger"
                ?disabled=${!this.canAct}
                @click=${() => (this.purging = true)}
              >
                ${this.t("purge")}
              </button>`
        }
      </section>
      <section class="section">
        <h3>${this.t("tests")}</h3>
        <p class="help">${this.t("testHelp")}</p>
        ${this.composer()}${this.draft.dirty ? html`<p class="help">${this.t("saveFirst")}</p>` : nothing}
        <div class="actions">
          <button ?disabled=${!this.canAct} @click=${() => this.test(false)}>
            ${this.t("preview")}</button
          ><button
            class="primary"
            ?disabled=${!this.canAct}
            @click=${() => this.test(true)}
          >
            ${this.t("send")}
          </button>
        </div>
        ${
          this.result
            ? html`<div class="result" aria-live="polite">
                <h3>${this.t(this.resultKind)}</h3>
                ${this.resultView(this.result)}
              </div>`
            : nothing
        }
      </section>
    </div>`;
  }
  private composer() {
    const request = this.request;
    return html`<div class="grid">
        ${this.field("id", request.notification_id, (value) => this.editRequest("notification_id", value))}${this.field("title", request.title, (value) => this.editRequest("title", value))}
      </div>
      <label
        >${this.t("message")}<textarea
          data-field="message"
          .value=${request.message}
          @input=${(event: Event) => this.editRequest("message", (event.target as HTMLTextAreaElement).value)}
        ></textarea>
      </label>
      <div class="grid">
        ${this.select("recipients", request.recipient_mode, ["selected", "all", "present", "absent", "nearest"], (value) => this.editRequest("recipient_mode", value as Request["recipient_mode"]))}${this.select("delivery", request.delivery, ["immediate", "when_available"], (value) => this.editRequest("delivery", value as Request["delivery"]))}
      </div>
      ${
        request.recipient_mode === "selected"
          ? this.choices(
              "people",
              request.person_entity_ids,
              this.config.persons
                .filter((person) => person.person_id)
                .map((person) => ({
                  id: person.person_id,
                  name: this.personName(person.person_id),
                })),
              (values) => this.editRequest("person_entity_ids", values),
            )
          : nothing
      }${request.recipient_mode === "nearest" ? html`<p class="help">${this.t("nearestHelp")}</p>` : nothing}
      <details>
        <summary>${this.t("directDevices")}</summary>
        ${this.choices("directDevices", request.mobile_device_ids, this.snapshot?.catalog.mobile_devices.map((device) => ({ id: device.device_id, name: device.name })) ?? [], (values) => this.editRequest("mobile_device_ids", values))}${this.choices("directNotify", request.notify_entity_ids, this.entities(["notify"]), (values) => this.editRequest("notify_entity_ids", values))}
      </details>
      ${this.choices(
        "channels",
        request.channels,
        ["mobile", "voice", "persistent"].map((id) => ({
          id,
          name: this.text(id),
        })),
        (values) => this.editRequest("channels", values),
      )}${this.check("respectSleep", request.respect_sleep, (value) => this.editRequest("respect_sleep", value))}${this.select("priority", request.priority, ["quiet", "normal", "important", "critical"], (value) => this.editRequest("priority", value as Request["priority"]))}
      <p class="help">${this.t("priorityHelp")}</p>
      ${this.field("iosSound", request.ios_sound ?? "", (value) => this.editRequest("ios_sound", value))}
      <p class="help">${this.t("iosSoundHelp")}</p>
      <details>
        <summary>${this.t("lifecycle")}</summary>
        <div class="grid">
          ${this.select("cycle", request.cycle_mode, ["update", "new"], (value) => this.editRequest("cycle_mode", value as Request["cycle_mode"]))}${this.field("expiration", request.expires_in, (value) => this.editRequest("expires_in", Number(value)), "number", { min: 0, step: "1" })}
        </div>
        ${this.check("resolveOnClear", request.resolve_on_clear, (value) => this.editRequest("resolve_on_clear", value))}
        <div class="grid">
          ${this.field("reminderInterval", request.reminder_interval ?? 0, (value) => this.editRequest("reminder_interval", Number(value)), "number", { min: 0, max: 86400, step: "1" })}
          ${this.field("reminderLimit", request.reminder_limit ?? 0, (value) => this.editRequest("reminder_limit", Number(value)), "number", { min: 0, max: 100, step: "1" })}
        </div>
        <p class="help">${this.t("reminderHelp")}</p>
      </details>
      <details>
        <summary>${this.t("advanced")}</summary>
        <div class="grid">
          ${this.field("image", request.image_url, (value) => this.editRequest("image_url", value))}${this.field("link", request.click_url, (value) => this.editRequest("click_url", value))}${this.entity("camera", request.camera_entity_id, ["camera"], (value) => this.editRequest("camera_entity_id", value))}${this.field("icon", request.icon, (value) => this.editRequest("icon", value))}${this.field("color", request.color, (value) => this.editRequest("color", value))}${this.field("timeout", request.timeout, (value) => this.editRequest("timeout", Number(value)), "number", { min: 0, step: "1" })}
        </div>
      </details>
      ${
        request.channels.includes("voice")
          ? html`<details open>
              <summary>${this.t("voice")}</summary>
              <p class="help">${this.t("voiceHelp")}</p>
              ${this.select("voiceMode", request.voice_mode, ["explicit", "occupied"], (value) => this.editRequest("voice_mode", value as Request["voice_mode"]))}${request.voice_mode === "explicit" ? this.choices("speakers", request.media_player_entity_ids, this.entities(["media_player"]), (values) => this.editRequest("media_player_entity_ids", values)) : nothing}
              <div class="grid">
                ${this.entity("tts", request.tts_entity_id, ["tts"], (value) => this.editRequest("tts_entity_id", value))}${this.field("language", request.tts_language, (value) => this.editRequest("tts_language", value))}${this.field("voiceMessage", request.voice_message, (value) => this.editRequest("voice_message", value))}${this.field("volume", request.volume ?? "", (value) => this.editRequest("volume", value === "" ? null : Number(value)), "number", { min: 0, max: 100, step: "1" })}
              </div>
            </details>`
          : nothing
      }
      <details>
        <summary>${this.t("buttons")} (${request.buttons.length})</summary>
        ${repeat(
          request.buttons,
          (_button, index) => index,
          (button, index) => this.buttonEditor(button, index),
        )}<button
          @click=${() => this.editRequest("buttons", [...request.buttons, { id: `button_${createId().slice(0, 8)}`, label: "", uri: "", actions: [], resolve: false }])}
        >
          ${this.t("addButton")}
        </button>
      </details>`;
  }
  private buttonEditor(button: Button, index: number) {
    const update = (updates: Partial<Button>) =>
      this.editRequest(
        "buttons",
        this.request.buttons.map((item, itemIndex) =>
          itemIndex === index ? { ...item, ...updates } : item,
        ),
      );
    return html`<div class="device">
      <div class="grid">
        ${this.field("buttonLabel", button.label, (value) => update({ label: value }), "text", { required: true })}${this.field("buttonId", button.id, (value) => update({ id: value }), "text", { required: true })}
      </div>
      ${this.select("buttonKind", button.uri ? "uriButton" : "actionButton", ["actionButton", "uriButton"], (value) => update(value === "uriButton" ? { uri: "/", actions: [], resolve: false } : { uri: "" }))}${
        button.uri
          ? this.field(
              "link",
              button.uri,
              (value) => update({ uri: value }),
              "text",
              { required: true },
            )
          : html`<div class="field">
                <span>${this.t("actions")}</span>${
                  customElements.get("ha-selector")
                    ? html`<ha-selector
                        .hass=${this.hass}
                        .selector=${{ action: {} }}
                        .value=${button.actions}
                        @value-changed=${(event: CustomEvent) => update({ actions: event.detail.value ?? [] })}
                      ></ha-selector>`
                    : html`<p class="help">${this.t("actionEditorHelp")}</p>
                        <small
                          >${this.t("actionsCount")}:
                          ${button.actions.length}</small
                        >`
                }
              </div>
              ${this.check("resolveAfter", button.resolve, (value) => update({ resolve: value }))}`
      }<button
        class="danger"
        @click=${() =>
          this.editRequest(
            "buttons",
            this.request.buttons.filter(
              (_item, itemIndex) => itemIndex !== index,
            ),
          )}
      >
        ${this.t("remove")}
      </button>
    </div>`;
  }
  private resultView(
    value: unknown,
    depth = 0,
  ): TemplateResult | typeof nothing {
    if (depth > 5 || value === undefined) return nothing;
    if (value === null) return html`—`;
    if (Array.isArray(value))
      return value.length
        ? html`<ul>
            ${value.map((item) => html`<li>${this.resultView(item, depth + 1)}</li>`)}
          </ul>`
        : html`<small>${this.t("noResults")}</small>`;
    if (typeof value === "object")
      return html`<dl>
        ${Object.entries(value as Record<string, unknown>)
          .filter(
            ([key]) =>
              ![
                "actions",
                "tokens",
                "action_tokens",
                "token",
                "request",
              ].includes(key),
          )
          .map(
            ([key, content]) =>
              html`<dt>${this.text(key)}</dt>
                <dd>${this.resultView(content, depth + 1)}</dd>`,
          )}
      </dl>`;
    return html`${typeof value === "boolean" ? this.t(value ? "yes" : "no") : this.text(String(value))}`;
  }
  protected render() {
    const language = resolveLanguage(this.locale);
    if (this.hass?.user?.is_admin === false || this.error === "forbidden")
      return html`<div class="empty" lang=${language} role="alert">
        <h2>Hano</h2>
        <p>${this.t("forbidden")}</p>
      </div>`;
    const showMenu =
      this.narrow || this.hass?.dockedSidebar === "always_hidden";
    return html`<header lang=${language}>
        ${
          showMenu
            ? html`<button
                class="sidebar-toggle"
                aria-label=${this.t("menu")}
                title=${this.t("menu")}
                @click=${() => this.dispatchEvent(new CustomEvent("hass-toggle-menu", { detail: { open: true }, bubbles: true, composed: true }))}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M3 6h18v2H3zm0 5h18v2H3zm0 5h18v2H3z"></path>
                </svg>
              </button>`
            : nothing
        }
        <div class="brand">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path
              d="M12 22a2 2 0 002-2h-4a2 2 0 002 2m6-6V11a6 6 0 00-5-5.91V4a1 1 0 00-2 0v1.09A6 6 0 006 11v5l-2 2v1h16v-1z"
            ></path>
          </svg>
          <h1>Hano</h1>
        </div>
        <nav aria-label="Hano">
          ${(["notifications", "people", "rooms", "settings"] as const).map(
            (page) =>
              html`<button
                aria-current=${this.page === page ? "page" : nothing}
                @click=${() => {
                  this.page = page;
                  this.message = "";
                }}
              >
                ${this.t(page)}
              </button>`,
          )}
        </nav>
      </header>
      ${this.error ? html`<div class="notice error" lang=${language} role="alert">${this.text(this.error)}${!this.snapshot ? html` <button @click=${() => void this.connect()}>${this.t("retry")}</button>` : nothing}</div>` : nothing}${this.message ? html`<div class="notice" lang=${language} role="status">${this.text(this.message)}</div>` : nothing}${this.draft.conflict ? html`<div class="notice error" lang=${language} role="alert">${this.t("conflict")}</div>` : nothing}
      <main lang=${language}>
        ${!this.snapshot ? html`<div class="empty" role="status">${this.t("loading")}</div>` : this.page === "notifications" ? this.notificationView() : this.page === "people" ? this.peopleView() : this.page === "rooms" ? this.roomsView() : this.settingsView()}
      </main>
      ${
        this.draft.dirty || this.draft.conflict
          ? html`<footer class="savebar" lang=${language}>
              <div class="grow">${this.t("unsaved")}</div>
              <button ?disabled=${this.saving} @click=${() => this.discard()}>
                ${this.t("discard")}</button
              ><button
                class="primary"
                ?disabled=${this.saving || this.draft.conflict}
                @click=${() => void this.save()}
              >
                ${this.t(this.saving ? "saving" : "save")}
              </button>
            </footer>`
          : nothing
      }`;
  }
}
customElements.define("hano-panel", HanoPanel);
