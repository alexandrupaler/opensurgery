import json


class Experiment:
    def __init__(self):
        self.name = ""

        self.props = {}

        """
        The number of T gates in the circuit
        """
        self.props["t_count"] = 0

        """
        The footprint is the total number
            of data qubits which includes
            - computational qubits
            - ancilla needed to intermediate between the computational qubits
        """
        self.props["footprint"] = 0

        # the total number of gates in the circuit
        # max_time_units
        self.props["depth_units"] = 0

        """
            For the purpose of lattice surgery layouts, the routing overhead is most of the times 50%
            This means that: 
                footprint = data_qubits + routing_overhead * data_qubits
                footprint = (1 + routing_overhead) * data_qubits
        """
        self.props["routing_overhead"] = 50

        # gate_err_rate
        self.props["physical_error_rate"] = 0.001

        self.props["bool_distance"] = False
        self.props["enforced_distance"]  = 0

        self.props["safety_factor"] = 99

        # For the estimation of the depth of a volume (see compute_execution_rounds()) either
        # option_A: the approximation using T_depth=T_count * multiplication_factor_for_Clifford_domination
        # option_B: the experiment["depth_units"] is used
        # option_A is more worst-case like, if for example the depth is only a rule-of-thumb calculation
        self.props["prefer_depth_over_t_count"] = False


    def to_json(self):
        obj = {}
        obj[self.name] = self.props
        return json.dumps(obj)


