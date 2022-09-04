def console_callback(method, i, t, y, step_size, difference, tolerance):
    """
    A callback function to print results to the console

    :param method: Method name
    :param i: Step number
    :param t: Independent variable
    :param y: Dependent variable
    :param step_size: Step size
    :param difference: Difference from the adjustable step size calculation
    :param tolerance: Tolerance for difference values
    """
    print(f"{method}: Step {i}: t = {t}, y = {y}, step size = {step_size}, diff = {difference}, "
          f"tolerance = {tolerance}")
