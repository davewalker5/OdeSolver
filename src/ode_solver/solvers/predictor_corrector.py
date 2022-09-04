from ode_solver.solvers.solver_base import SolverBase


class PredictorCorrector(SolverBase):
    def __init__(self, function, notify_callbacks, precision):
        super(PredictorCorrector, self).__init__(function, notify_callbacks, precision)

    def solve_step(self, t, y, step_size):
        """
        Given the current value of the independent variable and the solution, w, solve the next
        step

        :param t: Independent variable (time)
        :param y: Dependent variable (y)
        :param step_size: Step size in independent variable
        :return: Tuple of the updated independent and dependent variables
        """
        # Predict
        fy = self._function(t, y)
        tp = t + step_size
        yp = y + step_size * fy

        # Correct
        fyp = self._function(tp, yp)
        y = y + step_size * (fy + fyp) / 2
        return tp, y
