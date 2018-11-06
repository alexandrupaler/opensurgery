import os
import json
import prepare_circuit as pc
import layout as la
import visualise_layout as vla
import layer_map as lll

import cirqinterface as ci


def write_json(object_to_store):
    with open('layout.json', 'w') as outfile:
        json.dump(object_to_store, outfile)


def main():

    if not os.path.exists("stars"):
        os.makedirs("stars")

    print("Santa Barbara Surgery\n")

    interface = ci.CirqInterface()
    cirq_circuit = interface.random_circuit(10, 10)

    prep = pc.PrepareCircuit()
    gate_list = prep.parse_to_my_string_format(cirq_circuit)
    commands = prep.replace_gates_with_multibody(gate_list)

    # tests begin
    # commands = ["INIT 7", "MZZ 4 ANCILLA", "MXX ANCILLA 2"]
    # tests end

    print(commands)

    layer_map = lll.LayerMap()

    # this is the layout, which needs to be first initialised
    lay = None

    if not commands[0].startswith("INIT"):
        # first line should always be INIT
        print("ERROR: No INIT command for the layer map")
        return

    for command in commands:
        print(command)

        command_splits = command.split(" ")

        if command_splits[0] == "INIT":
            layer_map.setup_arrangement_one(int(command_splits[1]))
            lay = la.CubeLayout(layer_map)

        elif command_splits[0] == "NEED":
            sets = lay.create_distillation()
            lay.configure_operation(*sets)
            # simples solution for the moment
            # without doing any optimisation is:
            # - each time a distillation is needed, a box is placed
            # - all the following gates are delayed until the distillation has finished
            lay.move_current_time_coordinate_to_max_from_set(sets)
            lay.extend_data_qubits_to_current_time()

        elif command_splits[0] == "MZZ":
            # and this is the route
            sets = lay.create_ancilla_route((command_splits[1], command_splits[2]))
            lay.configure_operation(*sets)
            lay.increase_current_time_coordinate()

        elif command_splits[0] == "MXX":
            # for the moment no difference between MXX and MZZ
            sets = lay.create_ancilla_route((command_splits[1], command_splits[2]))
            lay.configure_operation(*sets)
            lay.increase_current_time_coordinate()
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
            continue



    # # lay.random_elements(10)
    # lay.place_manual()

    # lay.debug_layer_map()

    # lay.debug_all_paths()

    v_layout = vla.VisualiseLayout()
    json_result = v_layout.visualise_cube(lay, remove_noop=True)
    write_json(json_result)




if __name__ == "__main__":
    main()

