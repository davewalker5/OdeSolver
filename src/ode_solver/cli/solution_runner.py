from ode_solver.solvers.euler import Euler
from ode_solver.solvers.predictor_corrector import PredictorCorrector
from ode_solver.solvers.runge_kutta_4 import RungeKutta4
from ode_solver.utils.function_loader import load_module_from_string, get_function_from_module
from ode_solver.utils.integration_methods import IntegrationMethods
from ode_solver.utils.callbacks import console_callback


class SolutionRunner:
    def __init__(self):
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
        self.integrator = self.create_integrator(f, pre_hook, post_hook)
        self.solve(self.integrator)

    @property
    def history(self):
        """
        Return the history from the latest run

        :return: List of dictionaries containing the points in the solution
        """
        return self.integrator.history if self.integrator else None

    def create_integrator(self, f, pre_hook, post_hook):
        """
        Create an instance of the integration class

        :param f: Function to solve
        :return: Instance of the integrator
        """
        callbacks = [console_callback]
        method_id = IntegrationMethods.method_id(self.options["method"])
        if method_id == IntegrationMethods.EULER:
            integrator = Euler(f, pre_hook, post_hook, callbacks, 6)
        elif method_id == IntegrationMethods.PREDICTOR_CORRECTOR:
            integrator = PredictorCorrector(f, pre_hook, post_hook, callbacks, 6)
        else:
            integrator = RungeKutta4(f, pre_hook, post_hook, callbacks, 6)

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
