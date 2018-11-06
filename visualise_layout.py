'''
    This class takes a layout
'''
import layout as la

class VisualiseLayout:
    def __init__(self):
        print("visual debug")

    def get_color(self, op_type):
        if op_type == la.OperationTypes.NOOP:
            return "white"
        elif op_type == la.OperationTypes.USE_DISTILLATION:
            return "magenta"
        elif op_type == la.OperationTypes.USE_QUBIT:
            return "red"
        elif op_type == la.OperationTypes.USE_ANCILLA:
            return "yellow"

    def visualise_cube(self, layout, remove_noop):
        json2 = {"nodes": [], "links": []}

        # simple type checking
        if not isinstance(layout, la.CubeLayout):
            print("ERROR: This is not a layout!\n")
            return

        for i in range(layout.get_isize()):
            for j in range(layout.get_jsize()):
                for t in range(layout.get_tsize()):
                    op_id = layout.coordinates[i][j][t]

                    op_type = layout.operations_dictionary[op_id]["op_type"]
                    cell_id = layout.get_cell_id(i, j, t)
                    color = self.get_color(op_type)

                    filter
                    if op_type == la.OperationTypes.NOOP and remove_noop:
                        continue

                    sides = 60
                    # when default this means that the volume is not used
                    # ancillas do not rotate their X or Z
                    if op_type in [la.OperationTypes.NOOP, la.OperationTypes.USE_ANCILLA]:
                        sides = 63

                    node_value = {"id": cell_id, "fy": i, "fx": j, "fz": t, "c": color, "op": op_id, "s": sides}
                    json2["nodes"].append(node_value)

        for op_id in layout.operations_dictionary:
            operation = layout.operations_dictionary[op_id]
            for touch_id in operation["touches"]:

                touch_link = {"source": touch_id, "target": operation["touches"][touch_id], "c": "blue"}
                json2["links"].append(touch_link)

        return json2
