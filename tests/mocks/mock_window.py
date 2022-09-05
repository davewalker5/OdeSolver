class MockWindow:
    def __init__(self, events):
        self.event_index = 0
        self.events = events

    def refresh(self):
        pass

    def read(self):
        """
        Mock the read method

        :return: Tuple of the event name and the event values
        """
        event = self.events[self.event_index]
        self.event_index = self.event_index + 1
        return event["name"], event["values"]

    def close(self):
        pass
