import json


class Experiment:
    def __init__(self):
        self.name = ""

        self.props = {}

        self.props["volume"] = 0
        # max_logical_qubits
        self.props["footprint"] = 0

        # max_time_units
        self.props["depth_units"] = 0

        self.props["routing_overhead"] = 0

        # gate_err_rate
        self.props["physical_error_rate"] = 0.001

        self.props["bool_distance"] = False
        self.props["enforced_distance"]  = 0

        self.props["safety_factor"] = 99


    def to_json(self):
        obj = {}
        obj[self.name] = self.props
        return json.dumps(obj)

