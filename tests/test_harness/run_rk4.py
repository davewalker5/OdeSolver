import os
from src.ode_solver.utils.function_loader import load_module_from_file, get_function_from_module
from src.ode_solver.utils.console_callback import console_callback
from src.ode_solver.solvers.runge_kutta_4 import RungeKutta4
from src.ode_solver.utils.data_exchange import write_csv

if __name__ == "__main__":
    # Load the function to solve
    tests_folder = os.path.dirname(os.path.dirname(__file__))
    module_path = os.path.join(tests_folder, "data", "example_function_2.py")
    module = load_module_from_file(module_path, "function_to_solve")
    f = get_function_from_module(module, "f")

    # Solve using the fourth order Runge Kutta method with automatic
    # step-size adjustment
    rk4 = RungeKutta4(f, [console_callback], 6)
    rk4.solve_for_range(5, 0.5, 0.5, False, 0.01)
    write_csv(rk4.history, "rk4.csv")
