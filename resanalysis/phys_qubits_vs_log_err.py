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
        self.explanation = "The initial circuit is at position (1,1) and any optimization will change the " \
                           "volume and space factor. The final position will show how much resource savings " \
                           "can be expected. Darker colors are better."


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
        volume = experiment["volume"]
        p_err = experiment["physical_error_rate"]

        # parameters are collected by the plot var
        total_num_physical_qubits = parameters["total_num_physical_qubits"]

        data = []

        for i in range(len(self.global_v)):
            for j in range(len(self.global_s)):
                scaled_nr_log_qubits = math.ceil(nr_log_qubits * self.global_s[j])
                scaled_volume = math.ceil(volume * self.global_v[i])

                # this is the distance that fits on patch
                dist = Qentiana.max_distance_to_fit_log_qubits_on_phys_qubits(scaled_nr_log_qubits, total_num_physical_qubits)

                # the per log unit approximated failure is computed from the phys err rate and the distance
                err_per_log_unit = Qentiana.vba_p_logical(p_err, dist)

                # the entire volume will fail with this prob
                err_per_scaled_volume = self.total_err(err_per_log_unit, scaled_volume)

                # // maybe change names for this data array because different meaning of output
                data.append({
                    "x"             : self.global_s[j],
                    "y"             : self.global_v[i],
                    "distance"      : dist,
                    "indiv_error"   : err_per_log_unit,
                    "total_error"   : err_per_scaled_volume,
                    "total_volume"  : scaled_volume,
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
                    "dist"          : 0,
                    "indiv_error"   : 0,
                    "total_volume"  : 0,
                    "qubits_used"   : 0,
                    "total_error"   : 0
                })

        return data


    def color_interpretation(self, d):
        rgb = to_rgb(d["total_error"])
        return "rgb({},{},{})".format(rgb)

    def explain_data(self, data, experiment):
        return "Distance at point ({}, {}): {} <br>".format(data["x"], data["y"], data["dist"]) \
            + "error rate in unit cell: {} with a total volume of {} <br>".format(data["indiv_error"], data["total_volume"]) \
            + "Total success probability: {} <br>".format(data["total_error"])

