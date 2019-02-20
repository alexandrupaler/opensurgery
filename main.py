import os
import json
import prepare_circuit as pc
import layout as la
import visualise_layout as vla
import layer_map as lll
import patches_state as ps
import cube_to_physical as qre

import cirqinterface as ci


def write_json(object_to_store):
    with open('layout.json', 'w') as outfile:
        json.dump(object_to_store, outfile)

def process_multi_body_format(commands):
    """
    Entry point is a multibody measurement format
    :param commands: list of commands. Accepted are INIT, NEED A, MZZ, MXX, MZ, MX, S, H
    :return:
    """

def main():

    ''''
        Required for SKC compiler
        Not always necessary if the generated circuits are Clifford+T, for example
    '''
    # if not os.path.exists("stars"):
    #     os.makedirs("stars")

    print("OpenSurgery (version Santa Barbara)\n")

    interface = ci.CirqInterface()

    # cirq_circuit = interface.random_circuit(nr_qubits=10, nr_gates=10)

    cirq_circuit = interface.openfermion_circuit()

    prep = pc.PrepareCircuit()
    gate_list = prep.parse_to_my_string_format(cirq_circuit)

    gate_list = prep.decompose_arbitrary_rotations(gate_list)
    # print(gate_list)

    # take the gates to M?? commands
    commands = prep.replace_gates_with_multibody(gate_list)

    # for comm in commands:
    #     print(comm)

    print(len(commands))

    return

    # load from file
    # commands = prep.load_multibody_format()

    # tests begin
    # commands = ['INIT 10', 'NEED A', 'S 2', 'MXX 2 3', 'H 2', 'H 3', 'MXX 2 3', 'MZZ A 3']
    # commands = ['INIT 4', 'NEED A', 'MZZ A 0', 'MX A' , 'S ANCILLA', 'MXX ANCILLA 0', 'H 3', 'S 3', 'NEED A', 'MZZ A 3', 'MX A', 'S ANCILLA', 'MXX ANCILLA 3', 'S 3', 'H 3', 'H 3', 'S 3', 'NEED A', 'MZZ A 0 3 1 2', 'MX A', 'S ANCILLA', 'MXX ANCILLA 0 3 1 2', 'S 3', 'H 3', 'H 2', 'S 2', 'H 1', 'NEED A', 'MZZ A 2 1', 'MX A', 'S ANCILLA', 'MXX ANCILLA 2 1', 'S 2', 'H 2', 'H 1', 'H 0', 'S 0', 'H 3', 'S 3', 'MZZ 0 1 2 3', 'H 0', 'H 1', 'MZZ 0 1', 'H 0', 'H 3', 'MZZ 0 3']
    # tests end

    #
    # The STORAGE of QUBIT STATES
    #
    patches_state = ps.PatchesState()

    #
    # The LAYER MAP
    #
    layer_map = lll.LayerMap()

    # this is the layout, which needs to be first initialised
    lay = None

    if not commands[0].startswith("INIT"):
        # first line should always be INIT
        print("ERROR: No INIT command for the layer map")
        return


    for command in commands:
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
            lay = la.CubeLayout(layer_map)

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
            filtered_active_patches = filter_active_patches(lay, patches_state, filter_out=[])
            lay.move_current_time_coordinate_to_max_from_coordinates(sets, patches_state, filtered_active_patches)

            # the distilled A state is available
            patches_state.add_active_patch("A")

        elif command_splits[0] == "MZZ":
            # and this is the route
            touch_sides = (["Z"] * (len(command_splits) - 1))
            qubit_list = command_splits[1:]

            sets = lay.create_route_between_qubits(qubit_list, patches_state, touch_sides)
            lay.configure_operation(*sets)

            filtered_active_patches = filter_active_patches(lay, patches_state, filter_out=qubit_list)
            lay.move_current_time_coordinate_to_max_from_coordinates(sets, patches_state, filtered_active_patches)

        elif command_splits[0] == "MXX":
            # for the moment no difference between MXX and MZZ
            touch_sides = (["X"] * (len(command_splits) - 1))
            qubit_list = command_splits[1:3]

            sets = lay.create_route_between_qubits(qubit_list, patches_state, touch_sides)
            lay.configure_operation(*sets)

            filtered_active_patches = filter_active_patches(lay, patches_state, filter_out=qubit_list)
            lay.move_current_time_coordinate_to_max_from_coordinates(sets, patches_state, filtered_active_patches)

        elif (command_splits[0] == "S") or (command_splits[0] == "V"):
            # I will tread S and V the same
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
        # which, for the moment, are not explicitly drawn
        elif command_splits[0] == "MX":
            continue
        elif command_splits[0] == "MZ":
            continue
        elif command_splits[0] == "H":
            # this adds a decorator to the patch
            # if the cell does not exist, the decorator cannot be added

            # coordinates of the data qubit
            qubit_string = lay.layer_map.get_circuit_qubit_name(command_splits[1])
            qub1_coord = lay.layer_map.get_qubit_coordinate_2d(qubit_string)

            span_set = [(*qub1_coord, lay.current_time_coordinate)]
            sets = (la.OperationTypes.HADAMARD_QUBIT, span_set, [], [])
            lay.configure_operation(*sets)

            coordinates_all_active_patches = filter_active_patches(lay, patches_state, filter_out=command_splits[1:])

            lay.move_current_time_coordinate_to_max_from_coordinates(sets, patches_state, coordinates_all_active_patches)

        #
        # If this is a measurement that consumed the A state
        # then the state will not be available any more
        #
        if ("A" in command_splits) and command_splits[0].startswith("M"):
            patches_state.remove_active_patch("A")

        if ("ANCILLA" in command_splits) and command_splits[0].startswith("M"):
            patches_state.remove_active_patch("ANCILLA")

    # Visual Debug the layer map layout
    # lay.debug_layer_map()

    # Visual Debug the paths computed between ancilla patches
    # lay.debug_all_paths()

    """
        Estimate the resources
    """
    max_log_qubits = len(layer_map.get_potential_data_patches_coordinates_2d())
    max_log_qubits += len(layer_map.get_potential_ancilla_patches_coordinates_2d())

    # TODO: This is not really correct, because I need to send as parameter the depth of the geometry
    # TODO: Correct
    total_t_gates = commands.count("NEED A")
    res_values = qre.compute_physical_resources(total_t_gates, max_log_qubits)
    print("Resource estimation (qubits, time): ", res_values)

    # """
    # Write the layout to disk - for visualisation purposes
    # """
    # v_layout = vla.VisualiseLayout()
    # json_result = v_layout.visualise_cube(lay, remove_noop=True)
    # write_json(json_result)


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



