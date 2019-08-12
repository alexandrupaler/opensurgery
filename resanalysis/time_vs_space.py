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
        self.explanation = "Comparison of two different optimization heuristics (time OR space) in terms of resulting numbers of physical qubits" \
                           "necessary for logical data patches (distillations are not included). " \
                           "In blue areas time optimization is better. In green areas, space optimization is better." \


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
                    "dist_space_scale": ret_1["distance"],
                    "dist_time_scale": ret_2["distance"],
                    "nr_space_scale": ret_1["num_data_qubits"],
                    "nr_time_scale": ret_2["num_data_qubits"],
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
                    "dist_space_scale"  : 0,
                    "dist_time_scale": 0,
                    "nr_space_scale" : 0,
                    "nr_time_scale": 0,
                    "ratio"         : 0
                })

        return data


    def color_interpretation(self, data):

        ratio1 = 1
        ratio2 = 1

        if data["nr_space_scale"] != 0:
            ratio1 = data["nr_time_scale"] / data["nr_space_scale"]

        if data["nr_time_scale"] != 0:
            ratio2 = data["nr_space_scale"] / data["nr_time_scale"]

        ratio = min(ratio1, ratio2)

        component_green     = ratio
        component_red       = ratio
        component_blue      = ratio

        red = to_rgb(component_red)
        green = to_rgb(component_green)
        blue = to_rgb(component_blue)

        if ratio == ratio1:
            blue = 255
        else:
            green = 255

        return "rgb({}, {}, {})".format(red, green, blue)


    def explain_data(self, data, experiment):
        curr_time = math.ceil(data["y"] * experiment["depth_units"])
        curr_space = math.ceil(data["x"] * experiment["footprint"])

        return "{} {} -> {} <br>".format(data["x"], data["y"], data["ratio"]) \
               + "dist time: {} having a footprint of log qubits<br>".format(data["dist_time_scale"], curr_space) \
               + "dist space: {} for a time of {}<br>".format(data["dist_space_scale"], curr_time) \
               + "qub time: {}<br>".format(data["nr_time_scale"])\
               + "qub spc: {}<br>".format(data["nr_space_scale"])
            #    + "tradeoff time scaling threshold:{}<br>".format(data["x"] * data["y"])\
            #    + "min scaling should be below tradeoff threshold:{}<br>".format(data["dist_opt_space"])\


