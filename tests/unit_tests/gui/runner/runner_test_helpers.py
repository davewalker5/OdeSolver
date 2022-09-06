import os


def load_function_definition(filename):
    """
    Load one of the test function files

    :param filename: Name of the file to load - must exist in the "data" folder
    """
    tests_folder = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    function_file = os.path.join(tests_folder, "data", filename)
    with open(function_file, mode="rt", encoding="utf-8") as func_f:
        function_definition = func_f.read()

    return function_definition
