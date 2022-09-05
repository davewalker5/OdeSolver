import pytest
from ode_solver.gui.options import OptionReason
from ode_solver.gui.options.option_validator import apply_solution_limit_rules, apply_chart_scaling_rules, \
    apply_validity_rules


@pytest.fixture()
def invalid_options_limit():
    return [{"name": "limit", "reason": OptionReason.EMPTY}]


@pytest.fixture()
def invalid_options_steps():
    return [{"name": "steps", "reason": OptionReason.EMPTY}]


@pytest.fixture()
def invalid_options_steps_and_limit():
    return [
        {"name": "limit", "reason": OptionReason.EMPTY},
        {"name": "steps", "reason": OptionReason.EMPTY}
    ]


@pytest.fixture()
def chart_scaling_invalid_options():
    return [
        {"name": "chart_min_y", "reason": OptionReason.EMPTY},
        {"name": "chart_max_y", "reason": OptionReason.EMPTY},
        {"name": "chart_max_x", "reason": OptionReason.EMPTY},
    ]


@pytest.fixture()
def validity_rules_invalid_options():
    return [
        {"name": "limit", "reason": OptionReason.EMPTY},
        {"name": "chart_min_y", "reason": OptionReason.EMPTY},
        {"name": "chart_max_y", "reason": OptionReason.EMPTY},
        {"name": "chart_max_x", "reason": OptionReason.EMPTY},
        {"name": "tolerance", "reason": OptionReason.EMPTY}
    ]


def test_limit_errors_removed_if_steps_valid(invalid_options_limit):
    apply_solution_limit_rules(invalid_options_limit)
    assert 0 == len(invalid_options_limit)


def test_steps_errors_removed_if_limit_valid(invalid_options_steps):
    apply_solution_limit_rules(invalid_options_steps)
    assert 0 == len(invalid_options_steps)


def test_steps_and_limit_errors_not_removed_if_neither_specified(invalid_options_steps_and_limit):
    apply_solution_limit_rules(invalid_options_steps_and_limit)
    assert 2 == len(invalid_options_steps_and_limit)


def test_solution_limit_rules_only_affect_solution_limit_values(invalid_options_limit):
    invalid_options_limit.append({"name": "chart_min_y", "reason": OptionReason.EMPTY})
    assert 2 == len(invalid_options_limit)
    apply_solution_limit_rules(invalid_options_limit)
    assert 1 == len(invalid_options_limit)


def test_chart_scaling_rules(chart_scaling_invalid_options):
    apply_chart_scaling_rules(chart_scaling_invalid_options)
    assert 0 == len(chart_scaling_invalid_options)


def test_chart_scaling_rules_only_affect_charting_options(chart_scaling_invalid_options):
    chart_scaling_invalid_options.append({"name": "limit", "reason": OptionReason.EMPTY})
    assert 4 == len(chart_scaling_invalid_options)
    apply_chart_scaling_rules(chart_scaling_invalid_options)
    assert 1 == len(chart_scaling_invalid_options)


def test_validity_rules(validity_rules_invalid_options):
    apply_validity_rules(False, True, validity_rules_invalid_options)
    assert 0 == len(validity_rules_invalid_options)


def test_tolerance_required_if_adjusting_step_size(validity_rules_invalid_options):
    apply_validity_rules(True, True, validity_rules_invalid_options)
    assert 1 == len(validity_rules_invalid_options)
    assert "tolerance" == validity_rules_invalid_options[0]["name"]


def test_chart_limits_required_if_not_auto_scaling(validity_rules_invalid_options):
    apply_validity_rules(False, False, validity_rules_invalid_options)
    invalid_option_names = [v["name"] for v in validity_rules_invalid_options]
    assert 3 == len(invalid_option_names)
    assert "chart_max_x" in invalid_option_names
    assert "chart_min_y" in invalid_option_names
    assert "chart_max_y" in invalid_option_names
