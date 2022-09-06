from decimal import Decimal

A = Decimal("0.5")


def f(_, y):
    """
    dy/dx = Ay

    :param _: Independent variable (not used in this example)
    :param y: Dependent variable
    :return: Next value of the dependent variable
    """
    return A * y
