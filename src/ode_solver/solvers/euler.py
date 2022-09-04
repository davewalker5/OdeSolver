from ode_solver.solvers.solver_base import SolverBase


class Euler(SolverBase):
    def __init__(self, function, notify_callbacks, precision):
        super(Euler, self).__init__(function, notify_callbacks, precision)

    def solve_step(self, t, y, step_size):
        """
        Given the current value of the independent variable and the solution, w, solve the next
        step

        :param t: Independent variable (time)
        :param y: Dependent variable (y)
        :param step_size: Step size in independent variable
        :return: Tuple of the updated independent and dependent variables
        """
        # Perform the calculation
        y = y + step_size * self._function(t, y)
        t = t + step_size
        return t, y
