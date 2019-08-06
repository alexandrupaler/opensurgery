import math

from . import res_utils as resu
from . import cube_to_physical as qre

class TimeVsSpace:
    def __init__(self, t_count, max_logical_qubits):
        #
        self.nr_items = 100
        # log spaced volume scaling factor
        self.global_v = resu.local_logspace(-2, 2, self.nr_items)
        # scaling factor space
        self.global_s = resu.local_linspace(0.1, 2, self.nr_items)
        #
        self.explanation = "Comparison of two different optimization heuristics (time and space). " \
                           "In blue/green areas space optimization is better compared to the time optimization. " \
                           "Purple/red areas are not self-consistent (not allowed) and in white areas " \
                           "the time optimization is superior."


    def get_default_parameters(self):
            #
            self.parameters = {}


    def gen_data(self, experiment):
        volume_min = experiment.volume
        space_min = experiment.footprint
        p_err = experiment.physical_error_rate

        data = []

        for i in range(len(self.global_v)):
            for j in range(len(self.global_s)):
                space_param = math.ceil(self.global_s[j] * space_min)

                qre1 = qre.Qentiana(t_count = 0,
                                    max_logical_qubits = space_param,
                                    max_time_units = volume_min/space_param,
                                    gate_err_rate = p_err)
                ret_1 = qre1.compute_physical_resources()
                # ret_1 = calculate_total(volume_min, space_param, p_err)

                vol_param = math.ceil(self.global_v[i] * volume_min)
                qre2 = qre.Qentiana(t_count = 0,
                                    max_logical_qubits = space_min,
                                    max_time_units = vol_param / space_min,
                                    gate_err_rate = p_err)
                ret_2 = qre2.compute_physical_resources()
                # ret_2 = calculate_total(vol_param, space_min, p_err)

                ratio = ret_2["number_of_physical_qubits"] / ret_1["number_of_physical_qubits"]

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

        # analysis = resu.analysis(data)

        analysis = {"ok": True}

        if analysis["ok"]:
            component_green = 255
        else:
            component_red = 255

        return "rgb(" + str(resu.to_rgb(component_red))\
              + "," + str(resu.to_rgb(component_green)) \
              + "," + resu.to_rgb(component_blue) + ")"


# def compute_over_content(self, data):
    #     curr_volume = resu.approx_mult_factor(data.y, experiment.volume)
    #     curr_space = resu.approx_mult_factor(data.x, experiment.footprint)
    #
    #     content = ""
    #     content += data.x + " " + data.y + "->" + data.ratio + "<br>"
    #     content += "distance vol: " + data.dist_opt_vol + " having a hardware footprint of " + curr_space + " log qubits <br>"
    #     content += "distance space: " + data.dist_opt_space + " for a volume of " + curr_volume + "<br>"
    #
    #     content += "tradeoff time scaling threshold<br>" + (data.x * data.y) + "<br>"
    #     content += "minimum scaling should be below tradeoff threshold:<br>" + data.dist_opt_space + "<br>"
    #
    #     content += "<br>";
    #     content += "qub vol: " + data["nr_target_vol"] + "<br>"
    #     content += "qub spc: " + data["nr_target_space"] + "<br>"
    #
    #     return content