from ode_solver.solvers.euler import Euler
from ode_solver.solvers.predictor_corrector import PredictorCorrector
from ode_solver.solvers.runge_kutta_4 import RungeKutta4
from ode_solver.utils.function_loader import load_module_from_string, get_function_from_module
from ode_solver.utils.integration_methods import IntegrationMethods


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
        module = load_module_from_string(self.options["function"], "simulation_module")
        f = get_function_from_module(module, "f")
        pre_hook = get_function_from_module(module, "pre_hook")
        post_hook = get_function_from_module(module, "post_hook")
        self.integrator = self.create_integrator(f)
        self.solve(self.integrator, pre_hook, post_hook)

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

    def solve(self, integrator, pre_hook, post_hook):
        """
        Run the solution using the specified integrator

        :param integrator: Instance of the integrator to use to solve the equation
        :param pre_hook: Pre-simulation function or None
        :param post_hook: Post-simulation function or None
        """
        if pre_hook:
            pre_hook(self.options)

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

        if post_hook:
            post_hook(integrator.history)

    def normalise(self):
        """
        Normalise Y values on a scale of 0.0 to 1.0
        """
        # Normalise the run history
        self.integrator.normalise_y()

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
