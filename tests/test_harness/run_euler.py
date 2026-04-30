import os
from src.ode_solver.utils.function_loader import load_module_from_file, get_function_from_module
from src.ode_solver.utils.console_callback import console_callback
from src.ode_solver.solvers.euler import Euler
from src.ode_solver.utils.data_exchange import write_csv


if __name__ == "__main__":
    # Load the function to solve
    tests_folder = os.path.dirname(os.path.dirname(__file__))
    module_path = os.path.join(tests_folder, "data", "example_function.py")
    module = load_module_from_file(module_path, "function_to_solve")
    f = get_function_from_module(module, "f")

    # Solve using the Euler method with automatic step-size adjustment
    e = Euler(f, [console_callback], 6)
    e.solve_for_range(20, 0.25, 0.5, True, 0.01)
    write_csv(e.history, "euler.csv")
