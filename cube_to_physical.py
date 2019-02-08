"""
    Add some kind of computation to translate the total volume of a circuit
    to number of physical qubits and number of seconds (time unit)
"""


def compute_physical_resources(t_count, max_logical_qubits):
    """
        Implementation a la Austin
    """

    # t_count = 100000000  # Total number of T gates in algorithm.
    # max_logical_qubits = 100  # Maximum number of logical qubits, not including distillation, used at any point in the algorithm.

    """
        Parameters
    """
    # Gate error rate that sets how quickly logical errors are suppressed. 1e-3 means a factor of 10 suppression with each increase of d by 2.
    characteristic_gate_error_rate = 0.001
    # Time required to execute a single round of the surface code circuit detecting errors.
    total_surface_code_cycle_time_ns = 1000
    # Safety factor S means that whenever we wish to do N things reliably, we target a failure probability of 1/(SN).
    safety_factor = 99
    # d1 must be at least 15 to permit enough space for the state injection.
    l1_distillation_code_distance_d1 = 15
    # d2 could in principle be less than 15, but it seems unlikely you would actually want to do that. Max and default is 31.
    l2_distillation_code_distance_d2 = 23
    #
    #
    #
    # The same value as the characteristic gate error rate using the techniques of Ying Li.
    injected_d7_error = characteristic_gate_error_rate
    # The injected error rate +100 times the distance 7 logical error rate (this approximates the amount of distance 7 structure to do a T gate).
    l1_T_gate_error = injected_d7_error + 100*p_logical(characteristic_gate_error_rate, 7)
    # 1000 times the distance d1 logical error rate approximates the L1 Clifford preparation error.
    l1_Clifford_prep_error = 1000 * p_logical(characteristic_gate_error_rate, l1_distillation_code_distance_d1)
    # The distilled L1 T gate error rate plus the L1 Clifford preparation error rate.
    l1_output_error = l1_Clifford_prep_error + distillation_p_out(l1_T_gate_error, 1)
    #
    # The L1 output error rate +100 times the distance d1 logical error rate (this approximates the amount of distance d1 structure to do a T gate).
    l2_T_gate_error = l1_output_error + 100 * p_logical(characteristic_gate_error_rate, l1_distillation_code_distance_d1)
    # 1000 times the distance d2 logical error rate approximates the L2 Clifford preparation error.
    l2_Clifford_prep_error = 1000*p_logical(characteristic_gate_error_rate, l2_distillation_code_distance_d2)
    # The distilled L2 T gate error plus the L2 Clifford preparation error rate.
    l2_output_error = l2_Clifford_prep_error + distillation_p_out(l2_T_gate_error,1)
    # Safe target error per T gate.
    target_error_per_T_gate = 1/(safety_factor * t_count)
    #
    # Required number of distillation levels for this algorithm.
    number_of_distillation_levels = 2
    if l1_output_error < l2_output_error:
        number_of_distillation_levels = 1
    elif l2_output_error < target_error_per_T_gate:
        number_of_distillation_levels = 2
    else:
        number_of_distillation_levels = "3+, fail"
    #
    # Number of qubits associated with a single L1 distillation.
    l1_distillation_qubits = 32*2*(l1_distillation_code_distance_d1 ** 2)
    # Number of qubits associated with a single L2 distillation.
    l2_distillation_qubits = 32*2*(l2_distillation_code_distance_d2 ** 2)
    #
    # Note that if 2 levels of distillation are required, that will be a single L2 +8 L1 footprints.
    total_distillation_qubits = "fail"
    if number_of_distillation_levels == 1:
        total_distillation_qubits = l1_distillation_qubits
    elif number_of_distillation_levels == 2:
        total_distillation_qubits = 8 * l1_distillation_qubits + l2_distillation_qubits
    else:
        total_distillation_qubits = "fail"
    #
    # Total number of rounds of surface code error detection required to prepare the necessary number of T states.
    execution_rounds = "fail"
    if number_of_distillation_levels == 1:
        execution_rounds = 6.5 * l1_distillation_code_distance_d1 * t_count
    elif number_of_distillation_levels == 2:
        if l2_distillation_code_distance_d2 > 2 * l1_distillation_code_distance_d1:
            execution_rounds = 6.5 * l2_distillation_code_distance_d2 * t_count
        else:
            execution_rounds = 6.5 * 2 * l1_distillation_code_distance_d1 * t_count
    else:
        execution_rounds = "fail"
    #
    # Total time required to run the algorithm, assuming this can be totally determined by the number of T gates.
    execution_time_secs = "fail"
    if number_of_distillation_levels == 1 or number_of_distillation_levels == 2:
        execution_time_secs = execution_rounds * total_surface_code_cycle_time_ns * 0.000000001
    else:
        execution_time_secs = "fail"
    #
    # Execution time (hours)	5.42E+00
    # Execution time (days)	2.26E-01
    # Execution time (years)	6.18E-04
    # Algorithm execution rounds times the number of data qubits and their communication channels.
    total_data_rounds = "fail"
    if number_of_distillation_levels == 1 or number_of_distillation_levels == 2:
        total_data_rounds = 1.5 * max_logical_qubits * execution_rounds
    else:
        total_data_rounds = "fail"
    #
    target_error_per_data_round = "fail"  # Safe target error rate per data round.
    if number_of_distillation_levels == 1 or number_of_distillation_levels == 2:
        target_error_per_data_round = 1 / (safety_factor * total_data_rounds)
    else:
        target_error_per_data_round = "fail"
    #
    # Code distance required to achieve the safe target error rate per data round.
    data_code_distance = "fail"
    if number_of_distillation_levels == 1 or number_of_distillation_levels == 2:
        data_code_distance = distance(characteristic_gate_error_rate, target_error_per_data_round)
    else:
        data_code_distance = "fail"
    #
    # Total number of data qubits, including communication channels.
    num_data_qubits = "fail"
    if number_of_distillation_levels == 1 or number_of_distillation_levels == 2:
        # TODO: Update with correct number of patches
        # TODO: And correct height of the entire schedule
        num_data_qubits = 1.5 * max_logical_qubits * 2 * (data_code_distance ** 2)
    else:
        num_data_qubits = "fail"
    #
    # Total physical qubits required to run algorithm.
    total_qubits = "fail"
    if number_of_distillation_levels == 1 or number_of_distillation_levels == 2:
        total_qubits = total_distillation_qubits + num_data_qubits
    else:
        total_qubits = "fail"

    return total_qubits, execution_time_secs


"""
VBA from Austin's arxiv Excel
Do While translated to simple while, because condition was after DO
"""
def levels(p_in, p_out):
    n = 0
    while p_in > p_out:
        n = n + 1
        p_in = 35 * (p_in ** 3)
    # levels = n
    return n


def p_logical(p_gate, d):
    # p_logical = 0.1 * (100 * p_gate) ^ ((d + 1) / 2)
    return 0.1 * (100 * p_gate) ** ((d + 1) / 2)


def distance(p_gate, p_l):
    d = 3
    while p_logical(p_gate, d) > p_l:
        d = d + 2
    # distance = d
    return d


def distillation_p_out(p_in, xxx_levels):
    n = 0
    while n < xxx_levels:
        n = n + 1
        p_in = 35 * (p_in ** 3)
    # distillation_p_out = p_in
    return p_in