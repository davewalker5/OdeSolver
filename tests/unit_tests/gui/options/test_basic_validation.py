import pytest
from ode_solver.gui.options import OptionReason
from ode_solver.gui.options.option_validator import get_option_validity, determine_basic_validity, \
    remove_invalid_option


@pytest.fixture()
def options_for_validation():
    return {
        "option_1": {
            "prompt": "Option 1",
            "type": "text",
            "required": True
        },
        "option_2": {
            "prompt": "Option 2",
            "type": "text",
            "required": False
        },
        "option_3": {
            "prompt": "Option 3",
            "type": "text",
            "required": True
        }
    }


@pytest.fixture()
def values_for_validation():
    return {
        "option_1": "some value",
        "option_2": "",
        "option_3": "",
    }


@pytest.fixture()
def invalid_options():
    return [
        {
            "name": "invalid_1",
            "reason": OptionReason.EMPTY
        },
        {
            "name": "invalid_2",
            "reason": OptionReason.VALUE_ERROR
        }
    ]


def test_non_empty_mandatory_text_is_valid():
    v = get_option_validity("test", "Test", "text", True, "Some Value")
    assert "test" == v["name"]
    assert "Test" == v["display_name"]
    assert "text" == v["type"]
    assert v["required"]
    assert "Some Value" == v["value"]
    assert v["valid"]
    assert OptionReason.OK == v["reason"]


def test_empty_non_mandatory_text_is_valid():
    v = get_option_validity("test", "Test", "text", False, "")
    assert "test" == v["name"]
    assert "Test" == v["display_name"]
    assert "text" == v["type"]
    assert not v["required"]
    assert "" == v["value"]
    assert v["valid"]
    assert OptionReason.OK == v["reason"]


def test_empty_mandatory_text_is_invalid():
    v = get_option_validity("test", "Test", "text", True, "")
    assert "test" == v["name"]
    assert "Test" == v["display_name"]
    assert "text" == v["type"]
    assert v["required"]
    assert "" == v["value"]
    assert not v["valid"]
    assert OptionReason.EMPTY == v["reason"]


def test_existing_file_is_valid():
    v = get_option_validity("test", "Test", "file", False, __file__)
    assert "test" == v["name"]
    assert "Test" == v["display_name"]
    assert "file" == v["type"]
    assert not v["required"]
    assert __file__ == v["value"]
    assert v["valid"]
    assert OptionReason.OK == v["reason"]


def test_missing_file_is_invalid():
    v = get_option_validity("test", "Test", "file", False, "a_missing_file.txt")
    assert "test" == v["name"]
    assert "Test" == v["display_name"]
    assert "file" == v["type"]
    assert not v["required"]
    assert "a_missing_file.txt" == v["value"]
    assert not v["valid"]
    assert OptionReason.VALUE_ERROR == v["reason"]


def test_valid_decimal_is_valid():
    v = get_option_validity("test", "Test", "decimal", False, "67.3423")
    assert "test" == v["name"]
    assert "Test" == v["display_name"]
    assert "decimal" == v["type"]
    assert not v["required"]
    assert "67.3423" == v["value"]
    assert v["valid"]
    assert OptionReason.OK == v["reason"]


def test_invalid_decimal_is_invalid():
    v = get_option_validity("test", "Test", "decimal", False, "not_a_valid_decimal")
    assert "test" == v["name"]
    assert "Test" == v["display_name"]
    assert "decimal" == v["type"]
    assert not v["required"]
    assert "not_a_valid_decimal" == v["value"]
    assert not v["valid"]
    assert OptionReason.VALUE_ERROR == v["reason"]


def test_missing_mandatory_decimal_is_invalid():
    v = get_option_validity("test", "Test", "decimal", True, "")
    assert "test" == v["name"]
    assert "Test" == v["display_name"]
    assert "decimal" == v["type"]
    assert v["required"]
    assert "" == v["value"]
    assert not v["valid"]
    assert OptionReason.EMPTY == v["reason"]


def test_unchecked_checkbox_is_valid():
    v = get_option_validity("test", "Test", "checkbox", False, False)
    assert "test" == v["name"]
    assert "Test" == v["display_name"]
    assert "checkbox" == v["type"]
    assert not v["required"]
    assert not v["value"]
    assert v["valid"]
    assert OptionReason.OK == v["reason"]


def test_checked_checkbox_is_valid():
    v = get_option_validity("test", "Test", "checkbox", False, True)
    assert "test" == v["name"]
    assert "Test" == v["display_name"]
    assert "checkbox" == v["type"]
    assert not v["required"]
    assert v["value"]
    assert v["valid"]
    assert OptionReason.OK == v["reason"]


def test_list_selection_is_valid():
    v = get_option_validity("test", "Test", "list", False, "Some Value")
    assert "test" == v["name"]
    assert "Test" == v["display_name"]
    assert "list" == v["type"]
    assert not v["required"]
    assert "Some Value" == v["value"]
    assert v["valid"]
    assert OptionReason.OK == v["reason"]


def test_non_mandatory_empty_list_selection_is_valid():
    v = get_option_validity("test", "Test", "list", False, "")
    assert "test" == v["name"]
    assert "Test" == v["display_name"]
    assert "list" == v["type"]
    assert not v["required"]
    assert "" == v["value"]
    assert v["valid"]
    assert OptionReason.OK == v["reason"]


def test_mandatory_empty_list_selection_is_invalid():
    v = get_option_validity("test", "Test", "list", True, "")
    assert "test" == v["name"]
    assert "Test" == v["display_name"]
    assert "list" == v["type"]
    assert v["required"]
    assert "" == v["value"]
    assert not v["valid"]
    assert OptionReason.EMPTY == v["reason"]


def test_determine_basic_validity_ignoring_empty_values(options_for_validation, values_for_validation):
    invalid_options = determine_basic_validity(options_for_validation, True, values_for_validation)
    assert 0 == len(invalid_options)


def test_determine_basic_validity_not_ignoring_empty_values(options_for_validation, values_for_validation):
    invalid_options = determine_basic_validity(options_for_validation, False, values_for_validation)
    assert 1 == len(invalid_options)
    assert "option_3" == invalid_options[0]["name"]
    assert "Option 3" == invalid_options[0]["display_name"]
    assert "text" == invalid_options[0]["type"]
    assert invalid_options[0]["required"]
    assert "" == invalid_options[0]["value"]
    assert not invalid_options[0]["valid"]
    assert OptionReason.EMPTY == invalid_options[0]["reason"]


def test_determine_basic_validity_ignores_unrecognised_values(options_for_validation, values_for_validation):
    values_for_validation["unrecognised"] = "some value"
    invalid_options = determine_basic_validity(options_for_validation, False, values_for_validation)
    assert 1 == len(invalid_options)
    assert "option_3" == invalid_options[0]["name"]


def test_can_remove_invalid_option(invalid_options):
    assert 2 == len(invalid_options)
    remove_invalid_option(invalid_options, "invalid_1")
    assert 1 == len(invalid_options)


def test_cant_remove_invalid_option_if_reason_is_not_empty(invalid_options):
    assert 2 == len(invalid_options)
    remove_invalid_option(invalid_options, "invalid_2")
    assert 2 == len(invalid_options)


def test_remove_invalid_option_ignores_empty_list():
    remove_invalid_option([], "option_1")
    assert True
