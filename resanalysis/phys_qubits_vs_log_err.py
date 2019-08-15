import math

from .res_utils import local_linspace, local_logspace, to_rgb
from .cube_to_physical import Qentiana

class PhysicalQubitsVsLogicalError:
    def __init__(self):
        #
        self.nr_items = 100
        # log spaced volume scaling factor
        self.global_v = local_logspace(-2, 2, self.nr_items)
        # scaling factor space
        self.global_s = local_linspace(0.1, 2, self.nr_items)
        #
        self.title = "Error vs. Exact Number of Physical Qubits"
        #
        self.explanation = "How many logical qubits fit on a given number of physical qubits? Fitting more " \
                           "logical qubits increases the logical error rate for the total volume. Time is scaled on " \
                           "the vertical axis. Logical qubits on the horizontal axis. Darker is better (lower error " \
                           "rate). Red is inconsistent data (e.g. too few physical qubits for logical qubits)."


    def get_default_parameters(self):
        parameters = {}
        parameters["bool_update_plot"] = False
        parameters["total_num_physical_qubits"] = 500

        return parameters


    def total_err(self, per_unit_err, nr_units):
        # Given a per step error rate
        # calculate/approximate the total error of the computation
        # Equivalent1: The sum of probabilities of at least one (one or more) unit failing with per_unit_err
        # Equivalent2: none of the units fail
        return math.pow(1 - per_unit_err, nr_units)


    def gen_data(self, experiment, parameters = None):
        """
        :param experiment:
        :return:
        """
        nr_log_qubits = experiment["footprint"]
        time = experiment["depth_units"]
        p_err = experiment["physical_error_rate"]

        # parameters are collected by the plot var
        total_num_physical_qubits = parameters["total_num_physical_qubits"]

        data = []

        for i in range(len(self.global_v)):
            for j in range(len(self.global_s)):
                scaled_nr_log_qubits = math.ceil(nr_log_qubits * self.global_s[j])
                scaled_time = math.ceil(time * self.global_v[i]) * nr_log_qubits

                # this is the distance that fits on patch
                dist = Qentiana.max_distance_to_fit_log_qubits_on_phys_qubits(scaled_nr_log_qubits, total_num_physical_qubits)

                err_per_exec_round = -1
                err_per_scaled_volume = -1

                if dist != -1:
                    # the per log unit approximated failure is computed from the phys err rate and the distance
                    err_per_exec_round = Qentiana.vba_p_logical(p_err, dist)

                    execution_rounds = Qentiana.compute_number_of_rounds(elements = scaled_nr_log_qubits * scaled_time,
                                                                         element_distance = dist,
                                                                         element_units_in_time = 1)

                    # the entire volume will fail with this prob
                    err_per_scaled_volume = self.total_err(err_per_exec_round, execution_rounds)

                # // maybe change names for this data array because different meaning of output
                data.append({
                    "x"             : self.global_s[j],
                    "y"             : self.global_v[i],
                    "distance"      : dist,
                    "indiv_error"   : err_per_exec_round,
                    "total_error"   : err_per_scaled_volume,
                    "qubits_used"   : Qentiana.phys_qubits_for_all_log_qubits(scaled_nr_log_qubits, dist)

                })

        return data

    def empty_data(self):
        data = []
        for i in range(len(self.global_v)):
            for j in range(len(self.global_s)):
                # // maybe change names for this data array because different meaning of output
                data.append({
                    "x"             : self.global_s[j],
                    "y"             : self.global_v[i],
                    "distance"      : 0,
                    "indiv_error"   : 0,
                    "qubits_used"   : 0,
                    "total_error"   : 0
                })

        return data


    def color_interpretation(self, d):

        if d["total_error"] == -1:
            # this is an error - use red color
            return "rgb(255, 0, 0)"

        rgb = to_rgb(d["total_error"])
        return "rgb({},{},{})".format(rgb, rgb, rgb)


    def explain_data(self, data, experiment):
        return "Distance at point ({:.2f}, {:.2f}): {} <br>".format(data["x"], data["y"], data["distance"]) \
            + "error rate per data round {:.4f} <br>".format(data["indiv_error"]) \
            + "Total success probability: {:.4f} <br>".format(data["total_error"])