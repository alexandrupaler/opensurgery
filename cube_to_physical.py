"""
    Add some kind of computation to translate the total volume of a circuit
    to number of physical qubits and number of seconds (time unit)
"""
"""
    Implementation a la Austin
"""

import math

class Qentiana:
    def __init__(self, t_count, max_logical_qubits):
        """
        Constructor. Considers that T-count == T-depth
        :param t_count:
        :param max_logical_qubits:
        """

        """
            Parameters
        """
        self.parameters = {
                            # Gate error rate that sets how quickly logical errors are suppressed.
                            # 1e-3 means a factor of 10 suppression with each increase of d by 2.
                            "characteristic_gate_error_rate" : 0.001,
                            # Time required to execute a single round of the surface code circuit detecting errors.
                            "total_surface_code_cycle_time_ns": 1000,
                            # Safety factor S means that whenever we wish to do N things reliably,
                            # we target a failure probability of 1/(SN).
                            "safety_factor": 99,
                            # d1 must be at least 15 to permit enough space for the state injection
                            "l1_distillation_code_distance_d1": 15,
                            # d2 could in principle be less than 15, but it seems unlikely you would
                            # actually want to do that. Max and default is 31.
                            "l2_distillation_code_distance_d2": 31,
                            # Start with 7, but recompute it
                            "data_code_distance": 7,
                            # For the moment assume that the T-depth is not really the worst case in time
                            # Thus, the circuit is Clifford dominated and then its depth is longer
                            # Multiplication factor = 2. used in self.compute_data_code_distance()
                            "multiplication_factor_for_Clifford_domination" : 2}
        #
        #
        # hard coded dimensions of distillation
        # using the dimensions from https://arxiv.org/pdf/1808.06709.pdf
        # These units are distance agnostic
        self.dist_box_dimensions = {"x"             : 4,
                                    "y"             : 8,
                                    "t"             : 6.5,
                                    "distance"      : -1}

        self.t_count = t_count
        self.max_logical_qubits = max_logical_qubits

        # A scale is the ratio between data patch qubit distance and the distillation distance
        # It effectively says how many logical qubit patches of distance d
        # can be fitted along the sides of a distillation box
        #
        self.number_of_distillation_levels = self.compute_number_of_dist_levels()
        # lock value
        # self.number_of_distillation_levels = 1
        self.error_message = "none"
        if self.number_of_distillation_levels not in [1, 2]:
            # I do not know what this is, but should exit
            self.error_message = "----> Error! 3+ levels."
            print(self.error_message)

        """
            In case max 2 levels distillation
        """
        # update the key "distance" in self.dist_box_dimensions
        self.compute_distillation_box_distance()

        # Compute the data patch distance as an approximation starting from:
        # - T-count / T-depth
        # - number of logical qubits
        # - multiplication_factor_for_Clifford_domination
        self.compute_data_code_distance()


    def compute_dist_box_in_patch_units(self):
        factor = float(self.dist_box_dimensions["distance"]) / float(self.parameters["data_code_distance"])

        n_box_dimensions = {"x" : math.ceil(self.dist_box_dimensions["x"] * factor),
                            "y" : math.ceil(self.dist_box_dimensions["y"] * factor),
                            "t" : 30}#math.ceil(self.dist_box_dimensions["t"] * factor)}

        return n_box_dimensions

    def compute_number_of_dist_levels(self):
        #
        #
        char_gate_err = self.parameters["characteristic_gate_error_rate"]
        dist_l1 = self.parameters["l1_distillation_code_distance_d1"]
        dist_l2 = self.parameters["l2_distillation_code_distance_d2"]
        #
        # The same value as the characteristic gate error rate using the techniques of Ying Li.
        injected_d7_error = self.parameters["characteristic_gate_error_rate"]
        # The injected error rate +100 times the distance 7 logical error rate
        # (this approximates the amount of distance 7 structure to do a T gate).
        l1_T_gate_error = injected_d7_error + 100 * self.vba_p_logical(char_gate_err, 7)
        # 1000 times the distance d1 logical error rate approximates the L1 Clifford preparation error.
        l1_Clifford_prep_error = 1000 * self.vba_p_logical(char_gate_err,
                                                           dist_l1)
        # The distilled L1 T gate error rate plus the L1 Clifford preparation error rate.
        l1_output_error = l1_Clifford_prep_error + self.vba_distillation_p_out(l1_T_gate_error, xxx_levels = 1)
        #
        #
        # The L1 output error rate +100 times the distance d1 logical error rate
        # (this approximates the amount of distance d1 structure to do a T gate).
        l2_T_gate_error = l1_output_error + 100 * self.vba_p_logical(char_gate_err,
                                                                     dist_l1)
        # 1000 times the distance d2 logical error rate approximates the L2 Clifford preparation error.
        l2_Clifford_prep_error = 1000 * self.vba_p_logical(char_gate_err,
                                                           dist_l2)
        # The distilled L2 T gate error plus the L2 Clifford preparation error rate.
        l2_output_error = l2_Clifford_prep_error + self.vba_distillation_p_out(l2_T_gate_error, xxx_levels = 1)#aici nu trebuie un doi?

        # Safe target error per T gate.
        target_error_per_T_gate = 1 / (self.parameters["safety_factor"] * self.t_count)
        #
        # Required number of distillation levels for this algorithm.
        nr_levels = 2
        if l1_output_error < l2_output_error:
            nr_levels = 1
        elif l2_output_error < target_error_per_T_gate:
            nr_levels = 2
        else:
            nr_levels = "3+, fail"

        return nr_levels


    def compute_distillation_box_distance(self):
        """
            The footprint of L1 and L2 distillations is on the left. The right is the time axis execution.
            ----------------             __________  ____________________  __________
            |A1||A1||A1||A1|            |          ||                    ||          |
            ----------------            |          ||                    ||          |
            ----------------            |     A1   ||                    ||    B1    |
            |              |            |__________||                    ||__________|
            |      2       |                        |        2           |
            |              |             __________ |                    | __________
            ----------------            |          ||                    ||          |      ^
            ----------------            |     A1   ||                    ||    B1    |      |
            |B1||B1||B1||B1|            |          ||                    ||          |      |
            ----------------            |__________||____________________||__________|      | time axis
            After 8 L1 have been executed (on the sides marked with A and B), the next 7 are executed.
            Thus, when L2 is needed, the bounding box in time is determined by max(d2, 2*d1), because either
            a. L2 is not delayed - the L1 sequence can be executed parallel to the L2
            b. L2 is delayed - the L1 sequence takes longer than d2

            Because the L1 and L2 distillations have the same structure,
            the distance acts as a scaling factor of their volume.
        """

        dist_l1 = self.parameters["l1_distillation_code_distance_d1"]
        dist_l2 = self.parameters["l2_distillation_code_distance_d2"]

        """
            The L1 distillations are executed with d1
            The L2 distillations are executed with d2
            Practically, the sides of the footprint are [vertical: 2*8*d1 + 4*d2, horizontal:8*d2]
            We need the bounding box.
            For horizontal: the same discussion like when computing time_dimension
            For vertical: Instead of computing with floats, for the moment round to either 2*(2*8*d1) or 2*(4*d2)
        """

        chosen_distance_in_depth = -1

        if self.number_of_distillation_levels == 1:
            chosen_distance_in_depth = dist_l1

        if (self.number_of_distillation_levels == 2) and (dist_l2 > 2 * dist_l1):
            chosen_distance_in_depth = dist_l2

        if (self.number_of_distillation_levels == 2) and (dist_l2 <= 2 * dist_l1):
            chosen_distance_in_depth = 2 * dist_l1

        self.dist_box_dimensions["distance"] = chosen_distance_in_depth


    def compute_data_code_distance(self):
        """
            Compute data code distance. Consider the maximum number of units on the time axis
        :param t_count:
        :param max_logical_qubits:
        :return:
        """
        """
        Total number of rounds of surface code error detection required to prepare the necessary number of T states.
        T-count is T-depth when all T gates are sequential
        Each distillation has known number of units in time
        The distance has been computed in compute_distillation_scale_factor
        """
        execution_rounds = self.compute_number_of_rounds(elements=self.t_count,
                                                         element_distance=self.dist_box_dimensions["distance"],
                                                         element_units_in_time=self.dist_box_dimensions["t"])

        """
        Assume that the logical qubit patches are executed in a sequence
        Each logical qubit is ONE unit long
        And each unit has a distance of execution_rounds (from the distillations)
        """
        total_data_rounds = self.compute_number_of_rounds(elements=self.max_logical_qubits,
                                                          element_distance=execution_rounds,
                                                          element_units_in_time=1)

        total_data_rounds *= self.parameters["multiplication_factor_for_Clifford_domination"]

        target_error_per_data_round = 1 / (self.parameters["safety_factor"] * total_data_rounds)

        # Code distance required to achieve the safe target error rate per data round.
        self.parameters["data_code_distance"] = self.vba_distance(self.parameters["characteristic_gate_error_rate"],
                                                                  target_error_per_data_round)

    def compute_footprint_distillation_qubits(self):
        """
        Computes the total number of physical qubits necessary for the distillery
        :return:
        """
        footprint_units =  self.dist_box_dimensions["x"] *  self.dist_box_dimensions["y"]
        #
        # Number of qubits associated with a single L1 distillation.
        l1_dist_qubits = footprint_units * self.per_patch_qubits(self.parameters["l1_distillation_code_distance_d1"])
        # Number of qubits associated with a single L2 distillation.
        l2_dist_qubits = footprint_units * self.per_patch_qubits(self.parameters["l2_distillation_code_distance_d2"])
        #
        # Note that if 2 levels of distillation are required, that will be a single L2 + 8 L1 footprints.
        # See diagram above
        total_dist_qubits = "fail"
        if self.number_of_distillation_levels == 1:
            total_dist_qubits = l1_dist_qubits
        elif self.number_of_distillation_levels == 2:
            total_dist_qubits = 8 * l1_dist_qubits + l2_dist_qubits
        else:
            total_dist_qubits = "fail"

        return total_dist_qubits

    # def compute_physical_resources(t_count, max_logical_qubits):
    def compute_physical_resources(self, max_time_units = 0):

        """
            Compute the number of physical qubits
        """
        # Total number of data qubits, including communication channels.
        # Have unit dimensions -> (1*1)
        num_data_qubits = self.max_logical_qubits * (1*1) * self.per_patch_qubits(self.parameters["data_code_distance"])
        #
        # Total physical qubits required to run algorithm.
        total_qubits = self.compute_footprint_distillation_qubits() + num_data_qubits
        #
        """
            Compute the execution time
            Assume T-depth is the worst case
        """
        execution_rounds = self.compute_number_of_rounds(elements = self.t_count,
                                                         element_distance = self.dist_box_dimensions["distance"],
                                                         element_units_in_time = self.dist_box_dimensions["t"])
        if max_time_units != 0:
            execution_rounds = self.compute_number_of_rounds(elements = max_time_units,
                                                             element_distance = self.parameters["data_code_distance"],
                                                             element_units_in_time = 1)


        execution_time_secs = execution_rounds * self.parameters["total_surface_code_cycle_time_ns"] * 0.000000001

        return total_qubits, execution_time_secs


    """
        Counting utilities
    """

    def per_patch_qubits(self, distance):
        return 2 * (distance ** 2)

    def compute_number_of_rounds(self, elements, element_distance, element_units_in_time):
        """
        Computes for a number of sequentially executed elements, the number of error correction rounds.
        :param elements: number of elements (e.g. distillation procedures)
        :param element_distance: the distance of the surface code used for the considered element types
        :param element_units_in_time: number of units (agnostic of distance) in time
        :return:
        """
        return elements * element_distance * element_units_in_time

    """
    VBA from Austin's arxiv Excel
    Do While translated to simple while, because condition was after DO
    """

    def vba_levels(self, p_in, p_out):
        n = 0
        while p_in > p_out:
            n = n + 1
            p_in = 35 * (p_in ** 3)
        # levels = n
        return n


    def vba_p_logical(self, p_gate, d):
        return 0.1 * (100 * p_gate) ** ((d + 1) / 2)


    def vba_distance(self, p_gate, p_l):
        d = 3
        while self.vba_p_logical(p_gate, d) > p_l:
            d = d + 2
        # distance = d
        return d


    def vba_distillation_p_out(self, p_in, xxx_levels):
        n = 0
        while n < xxx_levels:
            n = n + 1
            p_in = 35 * (p_in ** 3)
        # distillation_p_out = p_in
        return p_in