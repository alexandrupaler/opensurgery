from enum import Enum

# are numpy arrays faster?
import numpy as np

class OperationTypes(Enum):
    NOOP = 0
    USE_QUBIT = 1  # measures stabilisers in the patch of loqical qubit
    USE_ANCILLA = 3
    USE_DISTILLATION = 7
    ######################
    ROTATE_QUBIT = 2 # ancilla qubits are not rotated (at least in this scheme) and therefore this is not applicable to them
    USE_S_GATE = 4
    MOVE_PATCH = 6
    HADAMARD_QUBIT = 8


class PlacementStatus(Enum):
    OK = 0
    NO_TIME = 1
    ALREADY_BUSY = 3
    NO_SPACE = 5

class OperationDetails:
    """
    The details of an operation. Type, which cells it spans, which data patches it touches...
    """
    def __init__(self, cell_id=0):
        # the type of the operation
        self.op_type = OperationTypes.NOOP

        # the default id of a cell in the 3D space of coordinates
        # self.spans = [0]
        self.spans = np.array([cell_id])

        # which data patches are touched by this operation?
        self.touches = {}

        # self.decorator = OperationTypes.NOOP


class OperationCollection:
    """
    This class is a time ordered list of IDs of OperationDetails which is attached to each cell in the coordinates
    There may be multiple operations on a cell -- for the moment
    For example: distance D operations represented as cubes
    But also of lesser distance operations: Logical Hadamard in distance zero (?)
    Or two operations, one following the other, of distance D/2
    Overall all operations should have total distance D
    """
    def __init__(self, first_operation_id=0):
        # self.operations = np.array([first_operation_id])
        self.operations = [first_operation_id]

        # Default value for this is 63
        # meaning that all sides of the cube are drawn in the color specified
        # meaning that there is no X operator tracked for this one
        self.sides_integer_value = 63

    def return_instant_op(self):
        """
        Does this list of operations include any distance_zero operation such as Hadamard?
        :return: the operation type. OperationTypes.NOOP if not
        """
        return OperationTypes.NOOP

    def has_single_noop(self, operations_dictionary):
        if len(self.operations) == 1:
            operation = operations_dictionary[self.operations[0]]
            if operation.op_type == OperationTypes.NOOP:
                return True

        return False

    def get_first_op_id(self):
        return self.operations[0]

    def replace_single_noop_with_other(self, other_id):
        self.operations[0] = other_id

    def append_operation(self, other_id):
        if len(self.operations) == 0:
            print("ERROR! append_operation should be called only when numbers of operations is larger than one.")
            return
        self.operations.append(other_id)

    def get_zero_length_ops(self, operations_dictionary):
        for op_id in self.operations:
            op = operations_dictionary[op_id].op_type
            if op in [OperationTypes.HADAMARD_QUBIT]:
                return op

        return OperationTypes.NOOP

    def get_non_zero_length_ops(self, operations_dictionary):
        ret = {}
        for op_id in self.operations:
            op = operations_dictionary[op_id].op_type
            if op not in [OperationTypes.HADAMARD_QUBIT]:
                ret[op_id] = op

        return ret