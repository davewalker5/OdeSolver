import os
from ode_solver import load_function_from_file, console_callback, Euler, write_csv


if __name__ == "__main__":
    # Load the function to solve
    tests_folder = os.path.dirname(os.path.dirname(__file__))
    module_path = os.path.join(tests_folder, "data", "example_function.py")
    f = load_function_from_file(module_path, "function_to_solve", "f")

    # Solve using the Euler method with automatic step-size adjustment
    e = Euler(f, [console_callback], 6)
    e.solve_for_range(20, 0.25, 0.5, True, 0.01)
    write_csv(e.history, "euler.csv")
