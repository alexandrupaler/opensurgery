'''
    This class takes a layout
'''
import layout as la

class VisualLayout:
    def __init__(self):
        print("visual debug")

    def get_color(self, op_type):
        if op_type == la.OperationTypes.DEFAULT:
            return "white"
        elif op_type == la.OperationTypes.USE_DISTILLATION:
            return "magenta"
        elif op_type == la.OperationTypes.USE_QUBIT:
            return "red"
        elif op_type == la.OperationTypes.USE_ANCILLA:
            return "yellow"

    def visualise_cube(self, layout):
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

                    if op_type == la.OperationTypes.USE_DISTILLATION:
                        op_id = 999

                    node_value = {"id": cell_id, "fy": i, "fx": j, "fz": t, "c": color, "op": op_id}
                    json2["nodes"].append(node_value)

        return json2
