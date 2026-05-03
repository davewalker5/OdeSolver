from ode_solver.solvers.runner_base import RunnerBase
from ode_solver.utils.live_table_callback import LiveTableCallback


class SolutionRunner(RunnerBase):
    def __init__(self, quiet):
        """
        Initialiser

        :param quiet: True to suppress console output
        """
        self.quiet = quiet

    def create_integrator(self, f):
        """
        Create an instance of the integration class

        :param f: Function to solve
        :return: Instance of the integrator
        """
        if not self.quiet:
            table = LiveTableCallback(title=self.options["chart_title"])
            callbacks = [table]
        else:
            callbacks = None

        return super().create_integrator(f, callbacks)
