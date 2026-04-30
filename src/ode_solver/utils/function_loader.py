import sys
import importlib

def load_module_from_string(function_definition, module_name):
    """
    Load the simulation module 

    :param function_definition: String containing the function definition
    :param module_name: Name of the module to create and load into
    :param function_name: Function name to return
    :return: Python module
    """
    # Create a new, named, module
    module_spec = importlib.util.spec_from_loader(module_name, loader=None)
    module = importlib.util.module_from_spec(module_spec)
    module_source = function_definition

    # Compile the source code into the new module
    exec(module_source, module.__dict__)
    sys.modules[module_name] = module
    globals()[module_name] = module

    return module


def load_module_from_file(filepath, module_name):
    """
    Load the simulation module

    :param filepath: Path to the Python script defining the function
    :param module_name: Name of the module to create and load into
    :param function_name: Function name to return
    :return: Python module 
    """
    # Load the source code
    with open(filepath, mode="rt", encoding="utf-8") as func_f:
        definition = func_f.read()

    return load_module_from_string(definition, module_name)


def get_function_from_module(module, function_name):
    """
    Given a python module, return the named function from it

    :param module: Python module
    :param function_name: Function name to return
    :return: Named function from the module or None
    """
    # The function should be an item in the module's dictionary
    return module.__dict__[function_name] if function_name in module.__dict__ else None
