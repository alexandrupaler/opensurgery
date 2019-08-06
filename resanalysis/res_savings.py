import math

from . import res_utils as resu
from . import cube_to_physical as qre

class ResourceSavings:
    def __init__(self, t_count, max_logical_qubits):
        #
        self.nr_items = 100
        # log spaced volume scaling factor
        self.global_v = resu.local_logspace(-2, 2, self.nr_items)
        # scaling factor space
        self.global_s = resu.local_linspace(0.1, 2, self.nr_items)
        #
        self.explanation = "The initial circuit is at position (1,1) and any optimization will change the " \
                           "volume and space factor. The final position will show how much resource savings " \
                           "can be expected. Darker colors are better."

    def get_default_parameters(self):
        #
        self.parameters = {}


    def gen_data(self, experiment):
        # // 2D Array
        # // take the globale experiment for the moment

        start_volume = experiment.volume
        start_space = experiment.footprint
        p_err = experiment.physical_error_rate

        data = []

        qre1 = qre.Qentiana(t_count=0,
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
                qre2 = qre.Qentiana(t_count=0,
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
        return "rgb(" + str(resu.to_rgb(d["ratio"])) + \
               "," + str(resu.to_rgb(d["ratio"])) + \
               "," + str(resu.to_rgb(d["ratio"])) + \
               ")"

    # MaigloeckchenData.prototype.compute_over_content = function(data)
    # {
    #     var curr_volume = approx_mult_factor(data.y, experiment.volume);
    #     var curr_space = approx_mult_factor(data.x, experiment.footprint);
    #
    #     content = "";
    #     content += data.x + " " + data.y + "->" + data.ratio + "<br>";
    #     content += "distance vol: " + data.dist_opt_vol + " having a hardware footprint of " + curr_space + " log qubits <br>";
    #     content += "distance space: " + data.dist_opt_space + " for a volume of " + curr_volume + "<br>";
    #
    #     content += "tradeoff time scaling threshold<br>" + (data.x * data.y) + "<br>";
    #     content += "minimum scaling should be below tradeoff threshold:<br>" + data.dist_opt_space + "<br>";
    #
    #     content += "<br>";
    #     content += "qub vol: " + data.nr_target_vol + "<br>";
    #     content += "qub spc: " + data.nr_target_space + "<br>";
    #
    #     return content;
    # }