import FreeSimpleGUI as sg
import traceback


def show_error_window(error_text):
    layout = [
        [sg.Text("A runtime error occurred:", font=("Any", 12, "bold"))],
        [sg.Multiline(
            error_text,
            size=(120, 25),
            font=("Courier New", 10),
            disabled=True,
            expand_x=True,
            expand_y=True,
            autoscroll=False,   # 👈 don't jump to bottom
        )],
        [sg.Button("Copy"), sg.Button("Close")]
    ]

    window = sg.Window(
        "ODE Solver Error",
        layout,
        modal=False,
        resizable=True,
        finalize=True,
    )

    while True:
        event, _ = window.read()
        if event in (sg.WIN_CLOSED, "Close"):
            break
        if event == "Copy":
            sg.clipboard_set(error_text)

    window.close()


def run_event_loop(window, callbacks):
    """
    Run the main-window event loop

    :param window: Window for which to run the event loop
    :param callbacks: Dictionary of callback functions
    """
    while True:
        try:
            # Get the next event and if it's a window closed event then break out
            event, values = window.read()
            if event == sg.WIN_CLOSED:
                break

            # Check to see if the event is in the callbacks. If not, it's ignored. Otherwise,
            # get the callback function. If it's none, break out. Otherwise, call the function
            if event in callbacks.keys():
                callback = callbacks[event]
                if callback:
                    exit_loop = callback(window, values)
                    if exit_loop:
                        break
                else:
                    break

        except Exception as exc:
            error_text = "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)

            )

            show_error_window(error_text)

    window.close()
