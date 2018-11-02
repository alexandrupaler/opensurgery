import os
import json
import prepare_circuit as pc
import layout as la
import visual_layout as vla
import logical_layout as lll

import cirqinterface as ci


def write_json(object_to_store):
    with open('layout.json', 'w') as outfile:
        json.dump(object_to_store, outfile)


def main():

    if not os.path.exists("stars"):
        os.makedirs("stars")

    print("Santa Barbara Surgery\n")

    prep = pc.PrepareCircuit()

    layer_map = lll.LogicalLayout(10, 10)

    lay = la.CubeLayout(layer_map)
    lay.random_elements(10)

    v_layout = vla.VisualLayout()
    json_result = v_layout.visualise_cube(lay)
    write_json(json_result)

    # interface = ci.CirqInterface()

if __name__ == "__main__":
    main()

