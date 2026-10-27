import type { Config, Request } from "./types";
export const copy = <T>(value: T): T => structuredClone(value);
export const emptyConfig = (): Config => ({
  persons: [],
  rooms: [],
  tts_entity_id: "",
  tts_language: "",
  history_days: 30,
  native_volume_entity_ids: [],
});
export const emptyRequest = (): Request => ({
  notification_id: "",
  title: "",
  message: "",
  recipient_mode: "selected",
  person_entity_ids: [],
  notify_entity_ids: [],
  mobile_device_ids: [],
  channels: ["mobile"],
  respect_sleep: true,
  delivery: "immediate",
  priority: "normal",
  ios_sound: "",
  reminder_interval: 0,
  reminder_limit: 0,
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
});
export class Draft {
  value = emptyConfig();
  base = emptyConfig();
  revision = 0;
  conflict = false;
  get dirty() {
    return JSON.stringify(this.value) !== JSON.stringify(this.base);
  }
  reset(value: Config, revision: number) {
    this.value = copy(value);
    this.base = copy(value);
    this.revision = revision;
    this.conflict = false;
  }
  receive(value: Config, revision: number) {
    if (revision < this.revision) return;
    if (!this.dirty) this.reset(value, revision);
    else if (revision !== this.revision) this.conflict = true;
  }
  acknowledge(sent: Config, saved: Config, revision: number) {
    // Only acknowledge the submitted draft. New edits remain dirty.
    if (JSON.stringify(this.value) === JSON.stringify(sent))
      this.value = copy(saved);
    this.base = copy(saved);
    this.revision = revision;
    this.conflict = false;
  }
}
export const toggle = (values: string[], value: string): string[] =>
  values.includes(value)
    ? values.filter((item) => item !== value)
    : [...values, value];
export function errorCode(error: unknown): string {
  return (error as { code?: string })?.code ?? "error";
}
