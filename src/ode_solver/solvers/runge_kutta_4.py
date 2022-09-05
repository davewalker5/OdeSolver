from ode_solver.solvers.solver_base import SolverBase


class RungeKutta4(SolverBase):
    def __init__(self, function, notify_callbacks, precision):
        super(RungeKutta4, self).__init__(function, notify_callbacks, precision)

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
        k1 = step_size * self._function(t, y)
        k2 = step_size * self._function(t + step_size / 2, y + k1 / 2)
        k3 = step_size * self._function(t + step_size / 2, y + k2 / 2)
        k4 = step_size * self._function(t + step_size, y + k3)
        y = y + (k1 + 2 * k2 + 2 * k3 + k4) / 6
        t = t + step_size
        return t, y
