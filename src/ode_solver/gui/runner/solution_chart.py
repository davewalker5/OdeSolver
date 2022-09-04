"""
The PySimpleGUI/Matplotlib integration. The code in this module draws on the advice from Jason
Yang in the following GitHub issue:

https://github.com/PySimpleGUI/PySimpleGUI/issues/5410
"""
from decimal import Decimal
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class Canvas(FigureCanvasTkAgg):
    """
    Implementation of a Matplotlib canvas under a tkinter/PySimpleGUI canvas
    """
    def __init__(self, figure=None, master=None):
        super().__init__(figure=figure, master=master)
        self.canvas = self.get_tk_widget()
        self.canvas.pack(side='top', fill='both', expand=1)


class SolutionChart:
    def __init__(self, canvas):
        """
        Initialiser

        :param options: Current simulation options
        :param canvas: PySimpleGUI canvas in which to draw the chart
        """
        # Chart data
        self.data_x = []
        self.data_y = []
        self.x_max = None
        self.y_min = None
        self.y_max = None
        self.title = ""

        # Drawing objects
        self.psg_canvas = canvas
        self.axes = None
        self.figure = None
        self.canvas = None

    def create_canvas(self):
        """
        Create a Matplotlib figure and canvas underlying a PySimpleGUI canvas
        """
        self.figure = Figure(dpi=100)
        self.canvas = Canvas(self.figure, self.psg_canvas.Widget)

    def create_axes(self, options):
        """
        Create a new set of axes (a plot or chart) in the current Matplotlib figure
        """
        # Remove the existing axes, if any, and create a new set
        self.figure.clf()
        self.axes = self.figure.add_subplot()

        # Get the axis scaling from the current options
        x_max = Decimal(options["chart_max_x"])
        y_min = Decimal(options["chart_min_y"])
        y_max = Decimal(options["chart_max_y"])
        self.axes.set(xlim=(0, x_max), ylim=(y_min, y_max))

    def initialise_chart(self, options):
        """
        Initialise the chart, removing any pre-existing chart first
        """
        # Create the canvas if not already done
        if not self.canvas:
            self.create_canvas()

        # Create a new set of axes (i.e. a plot)
        self.create_axes(options)

        # Initialise the chart X/Y data, axis limits and capture the title
        self.data_x = []
        self.data_y = []
        self.x_max = Decimal(options["chart_max_x"])
        self.y_min = Decimal(options["chart_min_y"])
        self.y_max = Decimal(options["chart_max_y"])
        self.title = options["chart_title"]

        # Draw the canvas to show the initial, empty, chart
        self.canvas.draw()

    def add_point(self, x, y):
        """
        Add a point to the chart and re-draw

        :param x: X-coordinate of point
        :param y: Y-coordinate of point
        """
        # Add the data point
        self.data_x.append(x)
        self.data_y.append(y)

        # Clear the axes and re-apply the labels (or the latter disappear) and scaling (or
        # the chart rescales repeatedly with each point addition)
        self.axes.cla()
        self.axes.set_title(self.title)
        self.axes.set_xlabel("x")
        self.axes.set_ylabel("y")
        self.axes.set(xlim=(0, self.x_max), ylim=(self.y_min, self.y_max))

        # Draw the grid and redraw the chart
        self.axes.grid()
        self.axes.plot(self.data_x, self.data_y)
        self.canvas.draw()
