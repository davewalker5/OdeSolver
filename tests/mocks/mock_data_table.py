class MockDataTable:
    def __init__(self):
        self._values = None

    @property
    def values(self):
        """
        Return the values generated by the solution runner
        """
        return self._values

    def update(self, values):
        """
        Mock the values update callback

        :param values: New data table values
        """
        self._values = values