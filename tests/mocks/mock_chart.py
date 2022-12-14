class MockChart:
    def __init__(self):
        self._points = []

    @property
    def points(self):
        """
        Return the points generated by the solution runner
        """
        return self._points

    def add_point(self, x, y):
        """
        Mock the point addition callback

        :param x: X-coordinate of point
        :param y: Y-coordinate of point
        """
        self._points.append({
            "x": x,
            "y": y
        })
