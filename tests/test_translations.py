"""All action fields, sections, options and button labels have complete translations."""

import json
from pathlib import Path

import pytest
from homeassistant.helpers import selector
from homeassistant.util.yaml import load_yaml

ROOT = Path(__file__).parents[1] / "custom_components" / "hano"


def leaves(value, prefix=""):
    if isinstance(value, dict):
        return {
            path
            for key, item in value.items()
            for path in leaves(item, f"{prefix}.{key}")
        }
    assert isinstance(value, str) and value.strip(), prefix
    return {prefix}


@pytest.mark.parametrize("language", ["en", "fr", "es"])
def test_translation_structure_and_action_fields(language):
    base = json.loads((ROOT / "strings.json").read_text())
    localized = json.loads((ROOT / "translations" / f"{language}.json").read_text())
    assert leaves(localized) == leaves(base)
    if language == "en":
        assert localized == base
    descriptions = load_yaml(str(ROOT / "services.yaml"))
    for action, value in descriptions.items():
        translated = localized["services"][action]
        for name, field in value["fields"].items():
            fields = field.get("fields", {name: field})
            if "fields" in field:
                assert translated["sections"][name]["name"]
            for key, spec in fields.items():
                assert translated["fields"][key]["name"]
                assert translated["fields"][key]["description"]
                selector.validate_selector(spec["selector"])
                choice = spec["selector"].get("select")
                if choice:
                    assert set(
                        localized["selector"][choice["translation_key"]]["options"]
                    ) == set(choice["options"])
    button = descriptions["send"]["fields"]["buttons"]["selector"]["object"]
    assert set(localized["selector"]["button"]["fields"]) == set(button["fields"])


def test_buttons_use_real_nested_action_selector():
    button = load_yaml(str(ROOT / "services.yaml"))["send"]["fields"]["buttons"][
        "selector"
    ]
    validate = selector.selector(button)
    actions = [{"action": "light.turn_off", "target": {"entity_id": "light.kitchen"}}]
    payload = [{"id": "done", "label": "Done", "actions": actions, "resolve": True}]
    assert validate(payload) == payload
