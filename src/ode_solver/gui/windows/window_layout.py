import PySimpleGUI as sg


def create_main_window(menu_definition):
    """
    Create the main GUI window

    :param menu_definition: Menubar definition
    """
    # Calculate the initial window size as a percentage of screen size
    screen_width, screen_height = sg.Window.get_screen_size()
    percentage_of_screen = 50
    canvas_width = int(percentage_of_screen * screen_width / 100)
    canvas_height = int(percentage_of_screen * screen_height / 100)

    # Main window has a tabbed dialog giving tabular and chart view onto the solution
    table_tab = sg.Tab(
        "Data Table",
        [[
            sg.Table(headings=["x", "y", "Step Size", "Difference"],
                     values=[],
                     display_row_numbers=True,
                     justification="center",
                     alternating_row_color='lightblue',
                     expand_x=True,
                     expand_y=True,
                     vertical_scroll_only=False,
                     key="table")
        ]],
        key="table_tab"
    )

    chart_tab = sg.Tab(
        "Chart",
        [[
            sg.Canvas(size=(canvas_width, canvas_height),
                      background_color="white",
                      key="chart",
                      expand_x=True,
                      expand_y=True)
        ]],
        key="chart_tab"
    )

    # Define the layout
    layout = [
        [sg.Menu(menu_definition, tearoff=False, pad=(0, 0))],
        [sg.TabGroup([[chart_tab, table_tab]], expand_x=True, expand_y=True)]
    ]

    # Create and return the window
    window = sg.Window("ODE Solver v1.1.1",
                       layout,
                       resizable=True,
                       margins=(0, 0),
                       finalize=True)
    window.TKroot.minsize(500, 300)
    return window


def create_options_dialog(current_options):
    """
    Create the simulation options dialog

    :param current_options: Current values and layout configuration information
    """
    tabs = []

    # Get a distinct, sorted set of tab names
    groups = sorted(set(o["group"] for o in current_options.values()))
    for group in groups:
        # Get the options in this tab and start the tab layout with a spacer
        group_options = {k: v for k, v in current_options.items() if v["group"] == group}
        group_layout = [[sg.Text("", size=(15, None))]]

        # Iterate over the options on this tab, creating the controls based on the properties
        # for each option (each operation equates to one row in the tab)
        for key, option in group_options.items():
            if option["type"] == "file":
                row = [sg.Text(option["prompt"], size=(15, None)),
                       sg.InputText(enable_events=option["events"], default_text=option["value"], key=key),
                       sg.Button("...")]
            elif option["type"] == "list":
                row = [sg.Text(option["prompt"], size=(15, None)),
                       sg.Combo(option["items"], enable_events=option["events"], default_value=option["value"],
                                key=key)]
            elif option["type"] == "checkbox":
                row = [sg.Checkbox(option["prompt"], enable_events=option["events"], default=option["value"], key=key)]
            elif option["type"] == "textarea":
                row = [sg.Multiline(size=(option["width"], option["height"]), font='courier 10',
                                    default_text=option["value"], key=key)]
            else:
                row = [sg.Text(option["prompt"], size=(15, None)),
                       sg.InputText(enable_events=option["events"], default_text=option["value"], key=key)]

            group_layout.append(row)

        # Finish the tab layout with a spacer then create a tab group from it and add it to the list
        # of tab groups
        group_layout.append([sg.Text("", size=(15, None))])
        group_tab = sg.Tab(group, group_layout, key=group)
        tabs.append(group_tab)

    # Greate the tab group and, below it, the buttons
    layout = [[sg.TabGroup([tabs])],
              [sg.Button("OK"), sg.Button("Cancel")]]

    # Create and return the dialog
    dialog = sg.Window("Options",
                       layout,
                       keep_on_top=True,
                       modal=True,
                       finalize=True)

    return dialog
