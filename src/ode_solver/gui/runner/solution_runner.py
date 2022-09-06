from ode_solver import Euler, PredictorCorrector, RungeKutta4, load_function_from_string
from ode_solver.gui.options import IntegrationMethods


class SolutionRunner:
    def __init__(self, chart, data_table, window):
        """
        Initialiser

        :param chart: Charting object for plotting the solution
        :param data_table: Data table control to write data to
        :param window: Calling window
        """
        # Solution options
        self.function = None
        self.options = None
        self.exception = None

        # Output controls
        self.window = window
        self.data_table = data_table
        self.chart = chart

        # Data to populate output controls
        self.data_table_content = []

        # Integrator
        self.integrator = None

    def run(self, options):
        """
        Run the solution
        """
        self.options = options
        f = load_function_from_string(self.options["function"], "function_to_solve", "f")
        self.integrator = self.create_integrator(f)
        self.solve(self.integrator)

    @property
    def history(self):
        """
        Return the history from the latest run

        :return: List of dictionaries containing the points in the solution
        """
        return self.integrator.history if self.integrator else None

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
        method_id = IntegrationMethods.method_id(self.options["method"])
        if method_id == IntegrationMethods.EULER:
            integrator = Euler(f, callbacks, 6)
        elif method_id == IntegrationMethods.PREDICTOR_CORRECTOR:
            integrator = PredictorCorrector(f, callbacks, 6)
        else:
            integrator = RungeKutta4(f, callbacks, 6)

        return integrator

    def solve(self, integrator):
        """
        Run the solution using the specified integrator
        """
        if self.options["limit"]:
            integrator.solve_for_range(self.options["limit"],
                                       self.options["step_size"],
                                       self.options["initial_value"],
                                       self.options["adjust_step_size"],
                                       self.options["tolerance"])
        else:
            integrator.solve_for_steps(self.options["steps"],
                                       self.options["step_size"],
                                       self.options["initial_value"])
