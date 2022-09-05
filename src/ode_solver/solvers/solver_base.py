from abc import abstractmethod
from decimal import Decimal, getcontext


class SolverBase:
    def __init__(self, function, notify_callbacks, precision):
        """
        Initialiser

        :param function: Function to solve
        :param notify_callbacks: List of notification callback for each step
        :param precision: Decimal precision
        """
        getcontext().prec = precision
        self._function = function
        self._history = []

        # Add the history recording callback to the notification callbacks
        self._notify_callbacks = notify_callbacks + [self.add_to_history] \
            if type(notify_callbacks) is list \
            else [self.add_to_history]

    def notify(self, i, t, y, step_size, difference, tolerance):
        """
        Call the notification callbacks for the current step in the solution

        :param i: Step number
        :param t: Independent variable
        :param y: Dependent variable
        :param step_size: Step in independent variable
        :param difference: Difference from the adjustable step size calculation
        :param tolerance: Tolerance for difference values
        """
        if self._notify_callbacks:
            for callback in self._notify_callbacks:
                callback(self.__class__.__name__, i, t, y, step_size, difference, tolerance)

    @property
    def history(self):
        """
        Return the history after a solution run

        :return: List of dictionaries containing the points in the solution
        """
        return self._history

    def add_to_history(self, method, i, t, y, step_size, difference, tolerance):
        """
        Add a point to the history

        :param method: Solver method name
        :param i: Step number
        :param t: Value of the independent variable
        :param y: Value of the dependent variable
        :param step_size: Step in independent variable
        :param difference: Difference from the adjustable step size calculation
        :param tolerance: Tolerance for difference values
        """
        self._history.append({
            "method": method,
            "step": i,
            "t": t,
            "y": y,
            "step_size": step_size,
            "difference": difference,
            "tolerance": tolerance
        })

    @abstractmethod
    def solve_step(self, t, y, step_size):
        """
        Abstract step solver - must be overridden in derived classes

        :param t: Independent variable
        :param y: Dependent variable
        :param step_size: Step size in the independent variable
        """
        pass

    def calculate_difference(self, t, y, step_size):
        """
        Calculate the difference in result between a single step and two half-steps

        :param t: Independent variable
        :param y: Dependent variable
        :param step_size: Starting step size
        :return: Tuple of updated time and dependent variable values and the difference
        """
        # Calculate using the full step size
        t1, y1 = self.solve_step(t, y, step_size)

        # Calculate using two half-steps
        half_step_size = step_size / 2
        ti, yi = self.solve_step(t, y, half_step_size)
        t2, y2 = self.solve_step(ti, yi, half_step_size)

        # Calculate the difference
        difference = abs(y2 - y1)

        return t1, y1, y2, difference

    def adjust_step_size(self, t, y, step_size, tolerance):
        """
        Adjust the step size to find one that is as large as possible while still
        giving a result that's within tolerance limits

        :param t: Independent variable
        :param y: Dependent variable
        :param step_size: Starting step size
        :param tolerance: Tolerance in the calculated values
        :return: Tuple of updated time, dependent variable and step size and the difference
        """
        t1, y1, y2, difference = self.calculate_difference(t, y, step_size)
        while difference > tolerance:
            step_size = step_size / 2
            t1, y1, y2, difference = self.calculate_difference(t, y, step_size)

        return t1, y1, step_size, difference

    def solve_for_range(self, limit, step_size, initial_value, variable_step, tolerance):
        """
        Solve the equation for the specified range of the independent variable,
        starting at t = 0

        :param limit: Maximum value of the independent variable
        :param step_size: Increment in the independent variable
        :param initial_value: Initial value of the dependent variable
        :param variable_step: If true, vary the step size to ensure an accurate solution
        :param tolerance: Maximum acceptable variance in calculated values
        """
        # Initialise, clear the history and notify of the initial value
        t = Decimal('0.0')
        y = Decimal(str(initial_value))
        limit_decimal = Decimal(str(limit))
        step_size_decimal = Decimal(str(step_size))
        tolerance_decimal = Decimal(str(tolerance)) if tolerance else Decimal("0")
        variable_step_multiplier = Decimal("1.5")
        current_step = 0
        self._history = []
        self.notify(0, t, y, step_size_decimal, 0, tolerance_decimal)

        # Iterate over the specified range of the independent variable
        while t <= limit_decimal:
            current_step = current_step + 1
            if variable_step:
                # For automatic step-size adjustment, start at the current step multiplied
                # by a suitable multiplier - this allows the step size to grow as well as
                # shrink, where appropriate
                tf, yf, step_size_decimal, difference = \
                    self.adjust_step_size(t, y, variable_step_multiplier * step_size_decimal, tolerance_decimal)
            else:
                tf, yf = self.solve_step(t, y, step_size_decimal)
                difference = Decimal("0")

            # Capture the new values at this step and send the new value notifications
            t, y = tf, yf
            self.notify(current_step, t, y, step_size_decimal, difference, tolerance_decimal)

    def solve_for_steps(self, steps, step_size, initial_value):
        """
        Solve the equation for the specified number of steps, starting at t = 0

        :param steps: Number of steps
        :param step_size: Increment in the independent variable
        :param initial_value: Initial value of the dependent variable
        """
        limit = (Decimal(steps) - 1) * Decimal(step_size)
        self.solve_for_range(limit, step_size, initial_value, False, 0)
