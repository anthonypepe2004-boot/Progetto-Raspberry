import json


class Observer:
    def __init__(self):
        self.messages = []

    def start_observing(self):
        pass

    def stop_observing(self):
        pass

    def dump_observed(self, observer_file):
        with open(observer_file, 'w') as f:
            json.dump(self.messages, f, indent=2)