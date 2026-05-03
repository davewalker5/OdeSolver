from ode_solver.solvers.euler import Euler
from ode_solver.solvers.predictor_corrector import PredictorCorrector
from ode_solver.solvers.runge_kutta_4 import RungeKutta4
from ode_solver.utils.function_loader import load_module_from_string, get_function_from_module
from ode_solver.utils.integration_methods import IntegrationMethods
from ode_solver.utils.live_table_callback import LiveTableCallback


class RunnerBase:
    def __init__(self):
        """
        Initialiser
        """
        self.options = None
        self.integrator = None

    def create_integrator(self, f, callbacks):
        """
        Create an instance of the integration class

        :param f: Function to solve
        :param callbacks: Callback functions
        :return: Instance of the integrator
        """
        method_id = IntegrationMethods.method_id(self.options["method"])
        if method_id == IntegrationMethods.EULER:
            integrator = Euler(f, callbacks, 6)
        elif method_id == IntegrationMethods.PREDICTOR_CORRECTOR:
            integrator = PredictorCorrector(f, callbacks, 6)
        else:
            integrator = RungeKutta4(f, callbacks, 6)

        return integrator

    def run(self, options):
        """
        Run the solution

        :param options: Set of simulation options to use
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
        self.integrator.normalise_y()
