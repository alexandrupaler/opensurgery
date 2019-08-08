import math

from .res_utils import local_logspace, local_linspace, to_rgb
from .cube_to_physical import Qentiana

class TimeVsSpace:
    def __init__(self):
        #
        self.nr_items = 100
        # log spaced volume scaling factor
        self.global_v = local_logspace(-2, 2, self.nr_items)
        # scaling factor space
        self.global_s = local_linspace(0.1, 2, self.nr_items)
        #
        self.title = "Time Vs Space"
        #
        self.explanation = "Comparison of two different optimization heuristics (time and space). " \
                           "In blue/green areas space optimization is better compared to the time optimization. " \
                           "Purple/red areas are not self-consistent (not allowed) and in white areas " \
                           "the time optimization is superior."


    def get_default_parameters(self):
        parameters = {}
        parameters["bool_update_plot"] = False

        return parameters


    def gen_data(self, experiment, parameters = None):
        volume_min = experiment["volume"]
        space_min = experiment["footprint"]
        p_err = experiment["physical_error_rate"]

        data = []

        for i in range(len(self.global_v)):
            for j in range(len(self.global_s)):
                space_param = math.ceil(self.global_s[j] * space_min)

                qre1 = Qentiana(t_count = 0,
                                    max_logical_qubits = space_param,
                                    max_time_units = volume_min/space_param,
                                    gate_err_rate = p_err)
                ret_1 = qre1.compute_physical_resources()
                # ret_1 = calculate_total(volume_min, space_param, p_err)

                vol_param = math.ceil(self.global_v[i] * volume_min)
                qre2 = Qentiana(t_count = 0,
                                    max_logical_qubits = space_min,
                                    max_time_units = vol_param / space_min,
                                    gate_err_rate = p_err)
                ret_2 = qre2.compute_physical_resources()
                # ret_2 = calculate_total(vol_param, space_min, p_err)

                ratio = ret_2["num_data_qubits"] / ret_1["num_data_qubits"]

                data.append({
                    "x": self.global_s[j],
                    "y": self.global_v[i],
                    "dist_opt_vol": ret_1["distance"],
                    "dist_opt_space": ret_2["distance"],
                    "nr_target_vol": ret_1["number_of_physical_qubits"],
                    "nr_target_space": ret_2["number_of_physical_qubits"],
                    "ratio": ratio,
                })

        return data


    def empty_data(self):
        data = []
        for i in range(len(self.global_v)):
            for j in range(len(self.global_s)):
                data.append({
                    "x"             : self.global_s[j],
                    "y"             : self.global_v[i],
                    "dist_opt_vol"  : 0,
                    "dist_opt_space": 0,
                    "nr_target_vol" : 0,
                    "nr_target_space": 0,
                    "ratio"         : 0
                })

        return data


    def color_interpretation(self, data):
        component_green     = data["ratio"]
        component_red       = data["ratio"]
        component_blue      = data["ratio"]

        red = to_rgb(component_red)
        green = to_rgb(component_green)
        blue = to_rgb(component_blue)

        # TODO: repair below instead of hardcoded
        # analysis = resu.analysis(data)
        analysis = {"ok": True}

        if analysis["ok"]:
            green = 255
        else:
            red = 255

        return "rgb({}, {}, {})".format(red, green, blue)


    def explain_data(self, data, experiment):
        curr_volume = math.ceil(data["y"] * experiment["volume"])
        curr_space = math.ceil(data["x"] * experiment["footprint"])

        return "{} {} -> {} <br>".format(data["x"], data["y"], data["ratio"]) \
               + "dist vol: {} having a footprint of log qubits<br>".format(data["dist_opt_vol"], curr_space) \
               + "dist space: {} for a volume of {}<br>".format(data["dist_opt_space"], curr_volume) \
               + "tradeoff time scaling threshold:{}<br>".format(data["x"] * data["y"])\
               + "min scaling should be below tradeoff threshold:{}<br>".format(data["dist_opt_space"])\
               + "qub vol: {}<br>".format(data["nr_target_vol"])\
               + "qub spc: {}<br>".format(data["nr_target_space"])


