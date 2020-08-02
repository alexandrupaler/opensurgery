import json
import prepare_circuit as pc
import layout as la
import visualise_layout as vla
import layer_map as lll
import patches_state as ps
import operationcollection as opc

import cirqinterface as ci

import time
import sys

from resanalysis import cube_to_physical as qre
from resanalysis.experiment import Experiment

def write_json(object_to_store):
    with open('layout.json', 'w') as outfile:
        json.dump(object_to_store, outfile)

def generate_random_circuits(random_configs):
    """
    Used for generating instances of random circuits that are going to be resource estimated
    :return:
    """

    intf = ci.CirqInterface()

    for expi in range(len(random_configs["qubits"])):
        # 100 trials for each circuit configuration
        for nrtrial in range(10):
            circ = intf.random_circuit(random_configs["qubits"][expi],
                                       random_configs["gates"][expi],
                                       random_configs["t_ratio"][expi])

            # save the circuit to a file
            fname = "random/rand_" + str((nrtrial,
                                          random_configs["qubits"][expi],
                                          random_configs["gates"][expi],
                                          random_configs["t_ratio"][expi])) + ".circ"
            fname = fname.replace(", ", "_")
            print(fname)
            with open(fname, 'w') as circfile:
                circfile.write(circ)


def load_random_circuits(random_configs):
    """
        Reads all the benchmarks into an array.
        It will be heavy on the memory
    """
    circuit_contents = []

    for expi in range(len(random_configs["qubits"])):
        # 100 trials for each circuit configuration
        for nrtrial in range(10):
            # save the circuit to a file
            fname = "random/rand_" + str((nrtrial,
                                          random_configs["qubits"][expi],
                                          random_configs["gates"][expi],
                                          random_configs["t_ratio"][expi])) + ".circ"
            fname = fname.replace(", ", "_")
            print("read file:" + fname)
            with open(fname, 'r') as circfile:
                # read entire file into string stored
                circuit_contents.append(circfile.read())

    return circuit_contents


def benchmark_layout_method():

    random_configs = {}
    random_configs["qubits"]  = [10,      20,     100,    200,    500]
    random_configs["gates"]   = [100,     100,    1000,   1000,   3000]
    random_configs["t_ratio"] = [50,      50,     50,     50,     50]
    #
    # random_configs["qubits"] = [100]
    # random_configs["gates"] = [10]
    # random_configs["t_ratio"] = [50]

    print("Random Circuits Benchmark")
    # use if new random benchmarks should be generated
    generate_random_circuits(random_configs)

    # load the benchmarking circuits
    benchmark_circuits = load_random_circuits(random_configs)

    for circuit in benchmark_circuits:
        print(".....")
        start = time.time()

        process_string_of_circuit(circuit)

        end = time.time()
        print("Time", end - start)
        sys.stdout.flush()


def main():

    ''''
        Required for SKC compiler
        Not always necessary if the generated circuits are Clifford+T, for example
    '''
    # if not os.path.exists("stars"):
    #     os.makedirs("stars")

    # benchmark_layout_method()
    # #
    # return

    print("OpenSurgery (version Santa Barbara)\n")

    interface = ci.CirqInterface()

    cirq_circuit = interface.random_circuit(nr_qubits=10, nr_gates=10)

    local_lay = process_string_of_circuit(cirq_circuit)

    visualise_layout(local_lay)


def process_string_of_circuit(qasm_cirq_circuit):

    # cirq_circuit = interface.openfermion_circuit()

    prep = pc.PrepareCircuit()
    gate_list = prep.parse_to_my_string_format(qasm_cirq_circuit)

    # A compaction of the SK decomposition would be good. Too many gates are output.
    # This will start an instance of the SKC decomposer
    gate_list = prep.decompose_arbitrary_rotations(gate_list)
    # print(gate_list)

    # take the gates to M?? commands
    commands = prep.replace_gates_with_multibody(gate_list)

    # print(len(commands))
    # print(commands)
    #
    # return

    # load from file
    # commands = prep.load_multibody_format()

    # tests begin
    # commands = ['INIT 2', 'NEED A']# 'MXX A 7', 'H 2', 'MX A', 'S ANCILLA', 'MX ANCILLA', 'ANCILLA 0']
    commands = ['INIT 10', 'NEED A', 'S 2', 'MXX 2 3', 'H 2', 'H 3', 'MXX 2 3', 'MZZ A 3']
    # commands = ['INIT 4', 'NEED A', 'MZZ A 0', 'MX A' , 'S ANCILLA', 'MXX ANCILLA 0', 'H 3', 'S 3', 'NEED A', 'MZZ A 3', 'MX A', 'S ANCILLA', 'MXX ANCILLA 3', 'S 3', 'H 3', 'H 3', 'S 3', 'NEED A', 'MZZ A 0 3 1 2', 'MX A', 'S ANCILLA', 'MXX ANCILLA 0 3 1 2', 'S 3', 'H 3', 'H 2', 'S 2', 'H 1', 'NEED A', 'MZZ A 2 1', 'MX A', 'S ANCILLA', 'MXX ANCILLA 2 1', 'S 2', 'H 2', 'H 1', 'H 0', 'S 0', 'H 3', 'S 3', 'MZZ 0 1 2 3', 'H 0', 'H 1', 'MZZ 0 1', 'H 0', 'H 3', 'MZZ 0 3']
    # tests end

    if not commands[0].startswith("INIT"):
        # first line should always be INIT
        print("ERROR: No INIT command for the layer map")
        return

    """
        Predict the resources
    """
    # data patches + ancilla patches + distillation patches
    # Assume number of patches equals qubits
    max_log_qubits = int(commands[0].split(" ")[1])
    t_count = commands.count("NEED A")

    # estimate the resources
    ex1 = Experiment()
    ex1.props["footprint"] = max_log_qubits
    ex1.props["t_count"] = t_count
    ex1.props["prefer_depth_over_t_count"] = False
    qentiana = qre.Qentiana(ex1.props)
    # res_values = qentiana.compute_physical_resources()
    # print("Resource prediction (levels, phys. qubits, time): ", res_values)

    #
    # The STORAGE of QUBIT STATES
    #
    patches_state = ps.PatchesState()

    #
    # The LAYER MAP
    #
    layer_map = lll.LayerMap(qentiana.compute_dist_box_in_patch_units())

    #
    # The LAYOUT, will be initialised after an INIT command
    #
    lay = None

    # determine the hardcoded time depth of a distillation and add some delay
    height_of_distillation = int(layer_map.distillation_t_length * 1)

    # worst case: each command is a distillation
    nr_commands = len(commands) * height_of_distillation


    # limit the maximum commands to nr_commands, because otherwise memory explodes
    for command in commands[0: nr_commands]:
        print(command)

        # each command should add a new time step?
        command_splits = command.split(" ")

        if ("ANCILLA" in command_splits) and (not patches_state.is_patch_active("ANCILLA")):
            patches_state.add_active_patch("ANCILLA")

        if command_splits[0] == "INIT":
            # pass patches_state to be filled by the method
            # with the names of the qubits that will be tracked
            layer_map.setup_arrangement_one(int(command_splits[1]), patches_state)

            # initialise the cubic layout
            lay = la.CubeLayout(layer_map, nr_commands)

            # for debugging purposes place some cubes to see if the layout is correct
            lay.debug_layer_map()

        elif command_splits[0] == "NEED":
            # add on time axis
            # lay.extend_data_qubits_to_current_time()

            sets = lay.create_distillation()
            lay.configure_operation(*sets)
            # simples solution for the moment
            # without doing any optimisation is:
            # - each time a distillation is needed, a box is placed
            # - all the following gates are delayed until the distillation has finished

            # Get the 2D coordinates of the active patches
            # filtered_active_patches = filter_active_patches(lay, patches_state, filter_out=[])
            # lay.move_curr_time_coord_to_max_from_coords(sets, patches_state, filtered_active_patches)

            # the distilled A state is available
            patches_state.add_active_patch("A")

        elif command_splits[0] == "MZZ":
            # and this is the route
            touch_sides = (["Z"] * (len(command_splits) - 1))
            qubit_list = command_splits[1:]

            sets = lay.create_route_between_qubits(qubit_list, patches_state, touch_sides)
            lay.configure_operation(*sets)

            filtered_active_patches = filter_active_patches(lay, patches_state, filter_out=qubit_list)
            lay.move_curr_time_coord_to_max_from_coords(sets, patches_state, filtered_active_patches)

        elif command_splits[0] == "MXX":
            # for the moment no difference between MXX and MZZ
            touch_sides = (["X"] * (len(command_splits) - 1))
            qubit_list = command_splits[1:3]

            sets = lay.create_route_between_qubits(qubit_list, patches_state, touch_sides)
            lay.configure_operation(*sets)

            filtered_active_patches = filter_active_patches(lay, patches_state, filter_out=qubit_list)
            lay.move_curr_time_coord_to_max_from_coords(sets, patches_state, filtered_active_patches)

        elif (command_splits[0] == "S") or (command_splits[0] == "V"):
            # I will treat S and V the same
            # for the moment not mark them with different colours

            # we need four patches in this method
            # two are ancilla, two are data
            # one of the data qubits (Q2) is moved on to an ancilla A3
            # A1 A2 A3
            # Q1 Q2
            # --------
            # A1 A2 Q2
            # Q1 A3
            # --------
            # QS QS  Q2
            # QS QS
            # --------
            # A1 A2 Q2
            # QS A3
            # --------
            # A1 A2 A3
            # QS Q2

            # add on time axis
            # lay.increase_current_time_coordinate()

            coordinates_all_active_patches = filter_active_patches(lay, patches_state, filter_out=[])

            sets = lay.create_s_gate(command_splits[1], patches_state, coordinates_all_active_patches)

        #
        #
        #
        # the following are time-depth zero operations
        # after their execution the patch is error corrected for time equal the distance
        # elif command_splits[0] == "MX":
        #     continue
        # elif command_splits[0] == "MZ":
        #     continue
        # elif command_splits[0] == "H":
        elif command_splits[0] in ["MX", "MZ", "H"]:
            # this adds a decorator to the patch
            # this is like worst case measurements - keep the qubits alive for another d, and only then measure
            # this is not really necessary...
            # if the cell does not exist, the decorator cannot be added

            # coordinates of the data qubit
            qubit_string = lay.layer_map.get_circuit_qubit_name(command_splits[1])
            qub1_coord = lay.layer_map.get_qubit_coordinate_2d(qubit_string)

            span_set = [(*qub1_coord, lay.current_time_coordinate)]

            curr_op_type = opc.OperationTypes.HADAMARD_QUBIT
            if command_splits[0] == "MX":
                curr_op_type = opc.OperationTypes.MX_QUBIT
            elif command_splits[0] == "MZ":
                curr_op_type = opc.OperationTypes.MZ_QUBIT

            sets = (curr_op_type, span_set, [], [])
            lay.configure_operation(*sets)

            coordinates_all_active_patches = filter_active_patches(lay, patches_state, filter_out=command_splits[1:])
            lay.move_curr_time_coord_to_max_from_coords(sets, patches_state, coordinates_all_active_patches)

            # if command_splits[0] in ["MX", "MZ"]:
            #     continue

        #
        # If this is a measurement that consumed the A state
        # then the state will not be available any more
        #
        if ("A" in command_splits) and (command_splits[0] in ["MX", "MZ"]):
            patches_state.remove_active_patch("A")

        if ("ANCILLA" in command_splits) and (command_splits[0] in ["MX", "MZ"]):
            patches_state.remove_active_patch("ANCILLA")

    # Visual Debug the layer map layout
    # lay.debug_layer_map()

    # Visual Debug the paths computed between ancilla patches
    # lay.debug_all_paths()

    return lay


def visualise_layout(lay):
    """
    Write the layout to disk - for visualisation purposes
    """
    v_layout = vla.VisualiseLayout()
    json_result = v_layout.visualise_cube(lay, remove_noop=True)
    write_json(json_result)


def filter_active_patches(lay, patches_state, filter_out=[]):
    names_strings = [lay.layer_map.get_circuit_qubit_name(x) for x in filter_out]
    # Get the 2D coordinates of the active patches
    filtered_active_patches = []

    for key in patches_state.get_all_active_patches():
        if not (key in names_strings):
            # coordinates_all_active_patches.append(lay.layer_map.get_qubit_coordinate_2d(key))
            filtered_active_patches.append(key)

    # coordinates_all_active_patches = lay.patch_names_to_coordinates(filtered_active_patches)
    # return coordinates_all_active_patches

    return filtered_active_patches

if __name__ == "__main__":
    # try:
    #     herr_interface.herr_write_file_1()
    # except:
    #     pass

    main()



