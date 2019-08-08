import sys
import math

from .res_utils import local_logspace, local_linspace_2
from .cube_to_physical import Qentiana

class DistanceBins:
    def __init__(self):
        self.nr_items = 101
        # // log spaced volume scaling factor
        self.x_axis_values = local_linspace_2(1, 0.5, self.nr_items)
        # scaling factor  space
        self.y_axis = local_logspace(2, 8, self.nr_items)
        #
        self.title = "Distance Bins"
        #
        self.explanation = "Tradeoff between volume and total number of " \
                           "physical qubits. Vertical lines are changes in distance."

        self.p___phys_err_rate = 0
        self.p___default_phys_err_rate = 0
        # experiment.physical_error_rate

        # 52 bit integers
        self.p___min_y = sys.maxsize
        self.p___max_y = -sys.maxsize - 1
        #
        # click detector
        self.p___just_clicked = True
        #
        self.reset_min_max_y()

        # A single console message. The same everywhere
        self.message = ""


    def get_default_parameters(self):
        parameters = {}
        parameters["bool_update_plot"] = True

        return parameters

    def reset_min_max_y(self):
        self.p___min_y = sys.maxsize
        self.p___max_y = -sys.maxsize - 1

    def store_min_max_y(self, y_val):
        self.p___min_y = min(y_val, self.p___min_y)
        self.p___max_y = max(y_val, self.p___max_y)

    def gen_data(self, experiment, parameters = None):
        volume_min = experiment["volume"]
        space_min = experiment["footprint"]
        p_err = experiment["physical_error_rate"]

        factor = (100 + experiment["routing_overhead"]) / 100

        data = []

        # stores the volume factors for which the distance changes
        dist_changes = []

        dist_last = -1
        volume_param = 0

        for i in range(len(self.x_axis_values)):
            volume_param = math.ceil(volume_min * self.x_axis_values[i])

            qre = Qentiana(t_count = 0,
                            max_logical_qubits = space_min,
                            max_time_units = volume_param/space_min,
                            gate_err_rate = p_err)
            ret = qre.compute_physical_resources()

            if (dist_last != -1) and (dist_last != ret["distance"]):
                dist_changes.append({
                    "x": self.x_axis_values[i],
                    "new_dist": ret["distance"]
                    })

            dist_last = ret["distance"]

            to_save_nr_qubits = ret["number_of_physical_qubits"]
            use_data_bus = False

            # Eliminate the ancillas means multiply by 1 / factor
            space_2 = math.ceil(space_min * (1 / factor))
            volume_2 = math.ceil(volume_param * (1 / factor))

            qre2 = Qentiana(t_count=0,
                           max_logical_qubits=space_2,
                           max_time_units=volume_2 / space_2,
                           gate_err_rate=p_err)
            ret_vol_2 = qre2.compute_physical_resources()

            #  Increase distance to lower res with data bus
            iterations = 0
            increased_distance = ret_vol_2["distance"]
            qubits_inc_dist = Qentiana.phys_qubits_for_all_log_qubits(space_2, increased_distance)

            while (qubits_inc_dist <= ret["number_of_physical_qubits"]) and (not use_data_bus):
                iterations+=1

                volume_inc_distance = volume_2 * increased_distance
                # space_min is not number of patches, but number of logical qubits, and the data bus counts as a qubit

                qre3 = Qentiana(t_count=0,
                                max_logical_qubits=space_min,
                                max_time_units=volume_inc_distance / space_min,
                                gate_err_rate=p_err)
                ret_3 = qre3.compute_physical_resources()

                if (ret_3["distance"] <= increased_distance):
                    # this number was calculated for the full layout without data bus
                    to_save_nr_qubits = qubits_inc_dist
                    use_data_bus = True
                else:
                    increased_distance += 2
                    qubits_inc_dist = Qentiana.phys_qubits_for_all_log_qubits(space_2, increased_distance)

            data.append({
                "x": self.x_axis_values[i],
                "number_of_physical_qubits": to_save_nr_qubits,
                "original_number_of_physical_qubits": ret["number_of_physical_qubits"],
                "dist": ret["distance"],
                "use_data_bus": use_data_bus
            })

            if self.x_axis_values[i] == 1.0:
                self.message = "At volume scaling {} with err rate {} <br>".format("1.0", experiment["physical_error_rate"]) \
                        + "there are savings ({}) if footprint overhead is reduced.".format(use_data_bus)

        self.update_y_axis(data)

        return {
            "data": data,
            "dist_changes": dist_changes
        }


    def update_y_axis(self, data):
        """
        Update y axis
        """
        if len(data) == 0:
            return

        self.reset_min_max_y()
        for i in range(len(data)):
            self.store_min_max_y(data[i]["number_of_physical_qubits"])
            self.store_min_max_y(data[i]["original_number_of_physical_qubits"])
        # recompute the values on the axis
        min_log = math.floor(math.log10(self.p___min_y))
        max_log = math.ceil(math.log10(self.p___max_y))
        if (max_log == min_log):
            max_log += 1
        self.y_axis = local_logspace(min_log, max_log, self.nr_items)


    def empty_data(self):
        data = []

        for i in range(len(self.x_axis_values)):
            data.append({
                "x": self.x_axis_values[i],
                "number_of_physical_qubits": 1,
                "original_number_of_physical_qubits": 1,
                "dist": 0,
                "use_data_bus": False
            })

        self.update_y_axis(data)

        ret = {
            "data" : data,
            "dist_changes": []
        }

        return ret

    def explain_data(self, data, experiment):
        # curr_volume = math.ceil(data["y"] * experiment["volume"])
        # curr_space = math.ceil(data["x"] * experiment["footprint"])

        return self.message

"""
From old source
"""
# bus_last_p_logical = -1
# bus_curr_p_logical = -1
# orig_last_p_logical = -1
# orig_curr_p_logical = -1
# # TODO: I think volumes and safety factors should be expressed in datarounds
# bus_last_p_logical = inv_target_error_per_data_round(
# comp_target_error_per_data_round_2(experiment.physical_error_rate, increased_distance),
# volume_inc_distance)
#
# orig_last_p_logical = inv_target_error_per_data_round(
# comp_target_error_per_data_round_2(experiment.physical_error_rate, ret.dist - 2),
# volume_param)

# bus_curr_p_logical = inv_target_error_per_data_round(
# comp_target_error_per_data_round_2(experiment.physical_error_rate, increased_distance),
# volume_inc_distance)
#
# orig_curr_p_logical = inv_target_error_per_data_round(
# comp_target_error_per_data_round_2(experiment.physical_error_rate, ret.dist),
# volume_param);

# increase_percentage = (qubits_inc_dist / ret.number_of_physical_qubits);
# if (this.x_axis_values[i] == 1.0) {
# this.console_text = "At volume scaling " + this.x_axis_values[i] + " with err rate " + experiment.physical_error_rate + "<br>";
#
# this.console_text += "increased by: " + increase_percentage + " compared to original distance " + ret.dist + "<br>";
# this.console_text += "bus_last_p_log: " + bus_last_p_logical + " bus_curr_p_log: " + bus_curr_p_logical + "<br>";
# this.console_text += "orig_last_p_log: " + orig_last_p_logical + " orig_curr_p_log: " + orig_curr_p_logical + "<br>";
#
# this.console_text += "use " + use_data_bus + " it:" + iterations + " from:" + ret_vol_2.dist + " to:" + increased_distance + " from:" + ret.number_of_physical_qubits + " to:" + qubits_inc_dist + "<br>";
#
# // console.log(this.console_text);
# }