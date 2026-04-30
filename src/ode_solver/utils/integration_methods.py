from enum import IntEnum


class IntegrationMethods(IntEnum):
    EULER = 0
    PREDICTOR_CORRECTOR = 1
    RUNGE_KUTTA_4 = 2

    @staticmethod
    def method_map():
        """
        Return a mapping between method IDs and names

        :return: Dictionary of method ID-name mappings
        """
        return {
            IntegrationMethods.EULER: "Euler",
            IntegrationMethods.PREDICTOR_CORRECTOR: "Predictor-Corrector",
            IntegrationMethods.RUNGE_KUTTA_4: "4th-Order Runge-Kutta"
        }

    @staticmethod
    def method_name_list():
        """
        Return a list of method names

        :return: List of method name strings
        """
        return [v for v in IntegrationMethods.method_map().values()]

    @staticmethod
    def method_name(method_id):
        """
        Return a method name given a method ID

        :param method_id: Method ID
        """
        return IntegrationMethods.method_map()[method_id]

    @staticmethod
    def method_id(method_name):
        """
        Return a method ID given a method name

        :param method_name: Method name
        """
        matches = [k for k, v in IntegrationMethods.method_map().items() if v == method_name]
        return matches[0]
