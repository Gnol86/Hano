import assert from "node:assert/strict";
import { test } from "node:test";
import { Draft, copy, emptyConfig, emptyRequest, toggle } from "../src/model";
import { en, fr, es, resolveLanguage, translate } from "../src/translations";
test("defaults use individual waiting opt-in, independent sleep and priority, no buttons", () => {
  const request = emptyRequest();
  assert.equal(request.respect_sleep, true);
  assert.equal(request.priority, "normal");
  assert.equal(request.delivery, "immediate");
  assert.deepEqual(request.buttons, []);
  assert.deepEqual(request.channels, ["mobile"]);
  assert.equal(request.expires_in, 0);
});
test("fresh config and request arrays do not leak mutations", () => {
  const a = emptyConfig();
  a.persons.push({
    person_id: "person.a",
    name: "",
    sleep_entity_id: "",
    devices: [],
  });
  assert.deepEqual(emptyConfig().persons, []);
  const b = emptyRequest();
  b.channels.push("voice");
  assert.deepEqual(emptyRequest().channels, ["mobile"]);
});
test("clean draft follows server revisions", () => {
  const draft = new Draft();
  draft.reset(emptyConfig(), 1);
  const config = emptyConfig();
  config.history_days = 60;
  draft.receive(config, 2);
  assert.equal(draft.value.history_days, 60);
  assert.equal(draft.dirty, false);
  assert.equal(draft.revision, 2);
});
test("concurrent revision preserves dirty values and exposes conflict", () => {
  const draft = new Draft();
  draft.reset(emptyConfig(), 1);
  draft.value.history_days = 60;
  draft.receive(emptyConfig(), 2);
  assert.equal(draft.value.history_days, 60);
  assert.equal(draft.conflict, true);
  assert.equal(draft.revision, 1);
});
test("same revision status events do not create conflicts", () => {
  const draft = new Draft();
  draft.reset(emptyConfig(), 1);
  draft.value.history_days = 60;
  draft.receive(emptyConfig(), 1);
  assert.equal(draft.conflict, false);
  assert.equal(draft.dirty, true);
});
test("acknowledgment preserves edits made while save is pending", () => {
  const draft = new Draft();
  draft.reset(emptyConfig(), 1);
  draft.value.history_days = 60;
  const sent = copy(draft.value);
  draft.value.history_days = 90;
  draft.acknowledge(sent, sent, 2);
  assert.equal(draft.value.history_days, 90);
  assert.equal(draft.base.history_days, 60);
  assert.equal(draft.dirty, true);
  assert.equal(draft.revision, 2);
});
test("successful save acknowledges only saved config and reset restores server", () => {
  const draft = new Draft();
  draft.reset(emptyConfig(), 1);
  draft.value.history_days = 60;
  const sent = copy(draft.value);
  draft.acknowledge(sent, sent, 2);
  assert.equal(draft.dirty, false);
  draft.value.history_days = 90;
  draft.reset(sent, 2);
  assert.equal(draft.value.history_days, 60);
});
test("stale snapshots cannot roll back configuration", () => {
  const draft = new Draft();
  draft.reset({ ...emptyConfig(), history_days: 90 }, 3);
  draft.receive(emptyConfig(), 1);
  assert.equal(draft.value.history_days, 90);
});
test("list toggles deduplicate and remove only selected item", () => {
  assert.deepEqual(toggle(["a", "b"], "a"), ["b"]);
  assert.deepEqual(toggle(["a"], "b"), ["a", "b"]);
});
test("all languages cover every product string", () => {
  assert.deepEqual(Object.keys(fr), Object.keys(en));
  assert.deepEqual(Object.keys(es), Object.keys(en));
  for (const catalog of [en, fr, es])
    for (const text of Object.values(catalog)) assert.ok(text.trim());
});
test("regional locales resolve consistently and unsupported locale falls back to English", () => {
  assert.equal(resolveLanguage("fr-BE"), "fr");
  assert.equal(resolveLanguage("es_MX"), "es");
  assert.equal(resolveLanguage("it"), "en");
  assert.equal(translate("save", "es-MX"), "Guardar");
  assert.equal(translate("save", "fr-CA"), "Enregistrer");
});
