export interface Device {
  type: "mobile" | "notify";
  target: string;
  platform: "ios" | "android" | "generic";
  device_id: string;
}
export interface Person {
  person_id: string;
  name: string;
  sleep_entity_id: string;
  devices: Device[];
}
export interface Room {
  id: string;
  name: string;
  presence_entity_id: string;
  sleep_entity_id: string;
  media_player_entity_ids: string[];
}
export interface Config {
  persons: Person[];
  rooms: Room[];
  tts_entity_id: string;
  tts_language: string;
  history_days: number;
  native_volume_entity_ids: string[];
}
export interface Button {
  id: string;
  label: string;
  uri: string;
  actions: Record<string, unknown>[];
  resolve: boolean;
}
export interface Request {
  notification_id: string;
  title: string;
  message: string;
  recipient_mode: "selected" | "all" | "present" | "absent" | "nearest";
  person_entity_ids: string[];
  notify_entity_ids: string[];
  mobile_device_ids: string[];
  channels: string[];
  respect_sleep: boolean;
  delivery: "immediate" | "when_available";
  priority: "quiet" | "normal" | "important" | "critical";
  cycle_mode: "update" | "new";
  expires_in: number;
  resolve_on_clear: boolean;
  image_url: string;
  click_url: string;
  camera_entity_id: string;
  icon: string;
  color: string;
  timeout: number;
  voice_mode: "explicit" | "occupied";
  media_player_entity_ids: string[];
  tts_entity_id: string;
  tts_language: string;
  voice_message: string;
  volume: number | null;
  buttons: Button[];
}
export interface Entity {
  entity_id: string;
  name: string;
  domain: string;
  state: string;
  attributes?: Record<string, unknown>;
}
export interface Mobile {
  service: string;
  name: string;
  device_id: string;
  platform: Device["platform"];
}
export interface Delivery {
  key: string;
  person_id: string;
  channel: string;
  target: string;
  status: string;
  reason: string;
  updated_at: string;
}
export interface Notification {
  notification_id: string;
  cycle_id: string;
  status: string;
  title: string;
  message: string;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  expires_at: string | null;
  request: Request;
  deliveries: Delivery[];
  history: { at: string; event: string; target?: string; detail?: unknown }[];
}
export interface Snapshot {
  version: string;
  revision: number;
  config: Config;
  notifications: Notification[];
  catalog: {
    entities: Entity[];
    mobile_services: Mobile[];
    mobile_devices: Mobile[];
    areas: { area_id: string; name: string }[];
  };
}
export interface Hass {
  language?: string;
  locale?: { language: string };
  user?: { is_admin: boolean };
  themes?: { darkMode: boolean };
  dockedSidebar?: string;
  panels?: Record<string, unknown>;
  connection: {
    subscribeMessage<T>(
      callback: (value: T) => void,
      message: Record<string, unknown>,
    ): Promise<() => void>;
  };
  callWS<T>(message: Record<string, unknown>): Promise<T>;
}
