import sys
import importlib


def load_function_from_file(filepath, module_name, function_name):
    """
    Load the function to be solved dynamically

    :param filepath: Path to the Python script defining the function
    :param module_name: Name of the module to create and load into
    :param function_name: Function name to return
    :return: Named function to be solved
    """
    # Create a new, named, module
    module_spec = importlib.util.spec_from_loader(module_name, loader=None)
    module = importlib.util.module_from_spec(module_spec)

    # Load the source code
    with open(filepath, mode="rt", encoding="utf-8") as func_f:
        module_source = func_f.read()

    # Compile the source code into the new module
    exec(module_source, module.__dict__)
    sys.modules[module_name] = module
    globals()[module_name] = module

    # The function should be an item in the module's dictionary
    return module.__dict__[function_name]
