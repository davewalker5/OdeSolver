def f(t, y):
    """
    dy/dx = x^2 * y -y

    :param t: Independent variable
    :param y: Dependent variable
    :return: Next value of the dependent variable
    """
    return t*t*y - y
