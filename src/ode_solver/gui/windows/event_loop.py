import PySimpleGUI as sg


def run_event_loop(window, callbacks):
    """
    Run the main-window event loop

    :param window: Window for which to run the event loop
    :param callbacks: Dictionary of callback functions
    """
    while True:
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

    window.close()
