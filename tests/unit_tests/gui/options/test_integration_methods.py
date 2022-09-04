from ode_solver.gui.options import IntegrationMethods


def test_can_get_method_map():
    method_map = IntegrationMethods.method_map()
    assert len(method_map) == 3


def test_euler_id_to_name():
    name = IntegrationMethods.method_name(IntegrationMethods.EULER)
    assert "Euler" == name


def test_euler_name_to_id():
    method_id = IntegrationMethods.method_id("Euler")
    assert IntegrationMethods.EULER == method_id


def test_predictor_corrector_id_to_name():
    name = IntegrationMethods.method_name(IntegrationMethods.PREDICTOR_CORRECTOR)
    assert "Predictor-Corrector" == name


def test_predictor_corrector_name_to_id():
    method_id = IntegrationMethods.method_id("Predictor-Corrector")
    assert IntegrationMethods.PREDICTOR_CORRECTOR == method_id


def test_rk4_id_to_name():
    name = IntegrationMethods.method_name(IntegrationMethods.RUNGE_KUTTA_4)
    assert "4th-Order Runge-Kutta" == name


def test_rk4_name_to_id():
    method_id = IntegrationMethods.method_id("4th-Order Runge-Kutta")
    assert IntegrationMethods.RUNGE_KUTTA_4 == method_id
