from ode_solver.solvers.runner_base import RunnerBase


class SolutionRunner(RunnerBase):
    def __init__(self, chart, data_table, window):
        """
        Initialiser

        :param chart: Charting object for plotting the solution
        :param data_table: Data table control to write data to
        :param window: Calling window
        """
        # Output controls
        self.window = window
        self.data_table = data_table
        self.chart = chart

        # Data to populate output controls
        self.data_table_content = []

    def refresh_window_callback(self, _method, _i, _t, _y, _step_size, _difference, _tolerance):
        """
        Callback to refresh the window as the solution progresses. The solution's on the main
        thread as the chart updates must happen on that thread

        :param _method: Method name
        :param _i: Step number
        :param _t: Independent variable
        :param _y: Dependent variable
        :param _step_size: Step size
        :param _difference: Difference from the adjustable step size calculation
        :param _tolerance: Tolerance for difference values
        """
        self.window.refresh()

    def data_table_callback(self, _method, _i, t, y, step_size, difference, _tolerance):
        """
        Insert a row into the data table

        :param _method: Method name
        :param _i: Step number
        :param t: Independent variable
        :param y: Dependent variable
        :param step_size: Step size
        :param difference: Difference from the adjustable step size calculation
        :param _tolerance: Tolerance for difference values
        """
        self.data_table_content.append([t, y, step_size, difference])
        self.data_table.update(values=self.data_table_content)

    def chart_callback(self, _method, _i, t, y, _step_size, _difference, _tolerance):
        """
        Add a point to the chart

        :param _method: Method name
        :param _i: Step number
        :param t: Independent variable
        :param y: Dependent variable
        :param _step_size: Step size
        :param _difference: Difference from the adjustable step size calculation
        :param _tolerance: Tolerance for difference values
        """
        self.chart.add_point(t, y)

    def create_integrator(self, f):
        """
        Create an instance of the integration class

        :param f: Function to solve
        :return: Instance of the integrator
        """
        callbacks = [self.data_table_callback, self.chart_callback, self.refresh_window_callback]
        return super().create_integrator(f, callbacks)

    def normalise(self):
        """
        Normalise Y values on a scale of 0.0 to 1.0
        """
        # Normalise the run history
        super().normalise()

        # Set Y-scale from 0 to 1.0
        self.options["chart_min_y"] = 0
        self.options["chart_max_y"] = 1.0
        self.options["chart_auto_scale"] = False

        # Re-initialise the chart
        self.chart.initialise_chart(self.options)

        # Re-plot each point
        for p in self.history:
            self.chart.add_point(p["t"], p["y_normalised"])
            self.window.refresh()
