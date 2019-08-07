import math

from .res_utils import local_logspace, local_linspace, to_rgb
from .cube_to_physical import Qentiana

class ResourceSavings:
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
        #
        parameters = {}
        parameters["bool_update_plot"] = False

        return parameters


    def gen_data(self, experiment, parameters = None):
        # // 2D Array
        # // take the globale experiment for the moment

        start_volume = experiment["volume"]
        start_space = experiment["footprint"]
        p_err = experiment["physical_error_rate"]

        data = []

        qre1 = Qentiana(t_count=0,
                            max_logical_qubits=start_space,
                            max_time_units=start_volume / start_space,
                            gate_err_rate=p_err)
        ret_1 = qre1.compute_physical_resources()

        for i in range(len(self.global_v)):
            for j in range(len(self.global_s)):
                #
                # Two types of scaling are considered simultaneously
                #
                # hardware is scaled
                space_param = math.ceil(self.global_s[j] * start_space)
                # time is scaled -> thus volume is increased
                vol_param = math.ceil(self.global_v[i] * start_volume)


                # If the initial volume is scaled like this
                qre2 = Qentiana(t_count=0,
                                    max_logical_qubits=space_param,
                                    max_time_units=vol_param / space_param,
                                    gate_err_rate=p_err)
                ret_2 = qre2.compute_physical_resources()

                ratio = ret_2["number_of_physical_qubits"] / ret_1["number_of_physical_qubits"]

                data.append({
                    "x"                 : self.global_s[j],
                    "y"                 : self.global_v[i],
                    "dist_opt_vol"      : ret_1["distance"],
                    "dist_opt_space"    : ret_2["distance"],
                    "nr_target_vol"     : ret_1["number_of_physical_qubits"],
                    "nr_target_space"   : ret_2["number_of_physical_qubits"],
                    "ratio"             : ratio
                })

        return data



    def empty_data(self):
        data = []
        for i in range(len(self.global_v)):
            for j in range(len(self.global_s)):
                data.append({
                    "x"                 : self.global_s[j],
                    "y"                 : self.global_v[i],
                    "dist_opt_vol"      : 0,
                    "dist_opt_space"    : 0,
                    "nr_target_vol"     : 0,
                    "nr_target_space"   : 0,
                    "ratio"             : 0
                })

        return data

    def color_interpretation(d):
        rgb = to_rgb(d["ratio"])
        return "rgb({},{},{})".format(rgb, rgb, rgb)

    def explain_data(self, data, experiment):
        curr_volume = math.ceil(data["y"] * experiment["volume"])
        curr_space = math.ceil(data["x"] * experiment["footprint"])

        return "{} {} -> {} <br>".format(data["x"], data["y"], data["ratio"]) \
               + "dist vol: {} having a footprint of log qubits<br>".format(data["dist_opt_vol"], curr_space) \
               + "dist space: {} for a volume of {}<br>".format(data["dist_opt_space"], curr_volume) \
               + "tradeoff time scaling threshold:{}<br>".format(data["x"] * data["y"]) \
               + "min scaling should be below tradeoff threshold:{}<br>".format(data["dist_opt_space"]) \
               + "qub vol: {}<br>".format(data["nr_target_vol"]) \
               + "qub spc: {}<br>".format(data["nr_target_space"])