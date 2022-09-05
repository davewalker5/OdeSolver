import pytest
import PySimpleGUI as sg
from tests.mocks import MockWindow
from ode_solver.gui.windows import run_event_loop

call_count = 0


def create_mock_events():
    events = []
    for i in range(0, 5):
        events.append({
            "name": str(i + 1),
            "values": {
                "ExitTheLoop": i == 4
            }
        })

    return events


@pytest.fixture()
def mock_events():
    return create_mock_events()


@pytest.fixture()
def mock_events_with_window_closed_event():
    events = create_mock_events()
    events[2]["name"] = sg.WIN_CLOSED
    return events


def mock_callback_function(window, values):
    global call_count
    call_count = call_count + 1
    return values["ExitTheLoop"]


def test_event_loop_runs_to_completion(mock_events):
    global call_count
    call_count = 0

    callbacks = {str(i): mock_callback_function for i in range(1, len(mock_events) + 1)}
    window = MockWindow(mock_events)

    run_event_loop(window, callbacks)
    assert len(mock_events) == call_count


def test_event_loop_ends_at_window_close_event(mock_events_with_window_closed_event):
    global call_count
    call_count = 0
    callbacks = {str(i): mock_callback_function for i in range(1, len(mock_events_with_window_closed_event) + 1)}

    window = MockWindow(mock_events_with_window_closed_event)
    run_event_loop(window, callbacks)

    assert 2 == call_count
    assert len(mock_events_with_window_closed_event) > call_count


def test_event_ends_at_none_callback(mock_events):
    global call_count
    call_count = 0
    callbacks = {str(i): None if i == 3 else mock_callback_function for i in range(1, len(mock_events) + 1)}

    window = MockWindow(mock_events)
    run_event_loop(window, callbacks)

    assert 2 == call_count
    assert len(mock_events) > call_count


def test_event_loop_ignores_unregistered_event(mock_events):
    global call_count
    call_count = 0
    callbacks = {str(i): mock_callback_function for i in range(1, len(mock_events) + 1)}

    mock_events.insert(2, {
        "name": "Unregistered",
        "values": {
            "ExitTheLoop": True
        }
    })

    window = MockWindow(mock_events)
    run_event_loop(window, callbacks)

    assert len(mock_events) - 1 == call_count
