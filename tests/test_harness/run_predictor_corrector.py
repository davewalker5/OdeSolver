import os
from src.ode_solver.utils.function_loader import load_module_from_file, get_function_from_module
from src.ode_solver.utils.callbacks import console_callback
from src.ode_solver.solvers.predictor_corrector import PredictorCorrector
from src.ode_solver.utils.data_exchange import write_csv


if __name__ == "__main__":
    # Load the function to solve
    tests_folder = os.path.dirname(os.path.dirname(__file__))
    module_path = os.path.join(tests_folder, "data", "example_function_3.py")
    module = load_module_from_file(module_path, "function_to_solve")
    f = get_function_from_module(module, "f")

    # Solve using the Euler predictor-corrector method with automatic
    # step-size adjustment
    pc = PredictorCorrector(f, [console_callback], 6)
    pc.solve_for_range(2, 0.2, 1, True, 0.0001)
    write_csv(pc.history, "predictor_corrector.csv")
