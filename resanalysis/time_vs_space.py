import math

from .res_utils import local_logspace, local_linspace, to_rgb
from .cube_to_physical import Qentiana
from .experiment import Experiment

class TimeVsSpace:
    def __init__(self):
        #
        self.nr_items = 100
        # log spaced volume scaling factor
        self.global_v = local_logspace(-2, 2, self.nr_items)
        # scaling factor space
        self.global_s = local_linspace(0.1, 2, self.nr_items)
        #
        self.title = "Time OR Space"
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
        time_orig = experiment["depth_units"]
        space_orig = experiment["footprint"]
        p_err = experiment["physical_error_rate"]

        data = []

        for i in range(len(self.global_v)):
            for j in range(len(self.global_s)):
                # Scale space
                ex1 = Experiment()
                ex1.props["footprint"] = math.ceil(self.global_s[j] * space_orig)
                ex1.props["depth_units"] = time_orig
                ex1.props["physical_error_rate"] = p_err
                ex1.props["prefer_depth_over_t_count"] = True
                qre1 = Qentiana(ex1.props)
                ret_1 = qre1.compute_physical_resources()

                # Scale time
                ex2 = Experiment()
                ex2.props["footprint"] = space_orig
                ex2.props["depth_units"] = math.ceil(self.global_v[i] * time_orig)
                ex2.props["physical_error_rate"] = p_err
                ex2.props["prefer_depth_over_t_count"] = True
                qre2 = Qentiana(ex2.props)
                ret_2 = qre2.compute_physical_resources()

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


