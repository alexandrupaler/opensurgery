'''
Here is a 3D matrix where elements represent certain operations
Operations have an id which is the value stored in the matrix


Associated to the matrix is a dictionary where the IDs are the keys and the values
are matrix coordinates (three dimensional), meaning where the operation (actually a usage of the
ancilla logical qubits) touches the data qubits.

Each entry in the matrix represents a d x d patch operated for d rounds
'''

from enum import Enum
import random

import layer_map as lll
import patches_state as ps


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
    def __init__(self):
        # the type of the operation
        self.op_type = OperationTypes.NOOP

        # the default id of a cell in the 3D space of coordinates
        self.spans = [0]

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


class CubeLayout:
    def __init__(self, lll_map):
        print("layout")

        self.layer_map = lll_map

        # default array is 0,0,1 in time with default op
        # self.coordinates = [[[0]]]
        self.coordinates = [[[OperationCollection(0)]]]

        # the default operation is null - nothing
        # the decorator refers to an operation that is instantaneous, like Measurements and Hadamards
        # self.operations_dictionary = {0: {"op_type": OperationTypes.NOOP,
        #                                   "spans": [0],
        #                                   "touches": {},
        #                                   "decorator": OperationTypes.NOOP}}
        self.operations_dictionary = {0: OperationDetails()}

        # used to increment the id of an operation
        self.operations_dictionary_id_incr = 1

        # default setup: cell 0,0,0 has id 0
        self.cell_dictionary = {(0, 0, 0): 0}

        self.current_time_coordinate = 0

        self.accommodate_hardware_sizes(lll_map.dimension_i, lll_map.dimension_j)

    def get_isize(self):
        return len(self.coordinates)

    def get_jsize(self):
        return len(self.coordinates[0])

    def get_tsize(self):
        return len(self.coordinates[0][0])

    def get_cell_id(self, si, sj, st):
        # not using ID from coordinates, but counting - is simpler to extend
        # search for the id at coordinates (si, sj, st)
        # for tup in self.cell_dictionary.items():
        #     if (si, sj, st) == tup[1]:
        #         return tup[0]
        return self.cell_dictionary[(si, sj, st)]

    def add_cell_id(self, si, sj, st):
        dict_key = (si, sj, st)
        if dict_key in self.cell_dictionary.keys():
            return self.cell_dictionary[dict_key]

        new_id = len(self.cell_dictionary) + 1

        self.cell_dictionary[dict_key] = new_id

        return new_id

    def add_op_id(self, new_op):
        # this is not a good way to give IDs, because dimension may change
        # new_id = len(self.operations_dictionary) + 1

        new_id = self.operations_dictionary_id_incr
        self.operations_dictionary_id_incr += 1

        self.operations_dictionary[new_id] = new_op
        return new_id

    def remove_op_id(self, old_id):
        if old_id in self.operations_dictionary:
            del self.operations_dictionary[old_id]
        else:
            print("ERROR!: Why was %s not in the operations dictionary?" % str(old_id))

    def add_time_coordinate(self):
        '''
        Inefficient way of adding another time slice
        :return: current time_coordinate
        '''
        for si in range(self.get_isize()):
            for sj in range(self.get_jsize()):
                self.add_NOOP(si, sj)

        return self.get_tsize()

    def increase_current_time_coordinate(self):
        if self.current_time_coordinate + 1 == self.get_tsize():
            self.add_time_coordinate()

        self.current_time_coordinate += 1

    def check_coordinate_span_set(self, span_set, time_offset=0):
        for coord in span_set:
            # check if time coordinate is ok
            if coord[2] + time_offset >= self.get_tsize():
                # problem - it goes outside of the available time
                return PlacementStatus.NO_TIME

            if (coord[0] >= self.get_isize()) or (coord[1] >= self.get_jsize()):
                # problem - it goes outside of the available space
                print("ERROR! The coordinate is out of hardware bounds: ->", coord)
                return PlacementStatus.NO_SPACE

            # get the object holding the collection of operations at the specified
            # 3D coordinate + the time offset of the operation one would like to place
            current_operation_collection = self.coordinates[coord[0]][coord[1]][coord[2] + time_offset]
            # if at this coordinate, there is something to execute
            # meaning that at these coordinates there is much more than a single NOOP placed
            # then the cell is already busy
            if not current_operation_collection.has_single_noop(self.operations_dictionary):
                return PlacementStatus.ALREADY_BUSY

        # everything went ok
        return PlacementStatus.OK

    def accommodate_object(self, span_set):
        # the total number of times the current_time_coordinate was advanced
        number_of_time_increases = 0
        placement_status = self.check_coordinate_span_set(span_set, number_of_time_increases)
        while placement_status != PlacementStatus.OK:
            if placement_status == PlacementStatus.ALREADY_BUSY:
                # not the time axis is the proble, but the fact that the cell is already occupied
                self.increase_current_time_coordinate()
                # update the time coordinates in the span_set
                number_of_time_increases += 1
            elif placement_status == PlacementStatus.NO_TIME:
                # there is no cell at this coordinate
                self.add_time_coordinate()
            elif placement_status == PlacementStatus.NO_SPACE:
                print("ERROR: No space! -- endless loop")
                return

            placement_status = self.check_coordinate_span_set(span_set, number_of_time_increases)

        return number_of_time_increases

    def update_coordinate_set_from_time_delta(self, coordinate_set, time_delta):
        for i in range(len(coordinate_set)):
            n_coord = (coordinate_set[i][0], coordinate_set[i][1], coordinate_set[i][2] + time_delta)
            coordinate_set[i] = n_coord
        return coordinate_set

    def transform_coordinate_set_into_index_set(self, coordinate_set):
        index_set = []
        for coord in coordinate_set:
            index = self.get_cell_id(*coord)
            index_set.append(index)
        return index_set

    def patch_names_to_coordinates(self, active_patches):
        ret = []
        for key in active_patches:
            ret.append(self.layer_map.get_qubit_coordinate_2d(key))
        return ret

    def move_current_time_coordinate_to_max_from_coordinates(self, coordinate_sets, patches_state, patches_to_extend_set=None):
        '''
        Assume that only one operation at a time is processed
        This means that the coordinates of this operation are between current_time_coordinate and the maximum time
        coordinate of the 3D cells defining the operation

        :param coordinate_sets: set of 3D coordinates representing the implemented operation
        :param patches_to_extend_set: the set of data patches which need to be extended along the operation
        which was applied. It may happen, that the patches refer also to coordinates where an operation is applied
        In that case, the extension is not made, because the cell is already occupied -> there will be a placement
        error ALREADY_BUSY
        :return: for the moment, nothing
        '''

        coord_patches_to_extend_set = self.patch_names_to_coordinates(patches_to_extend_set)

        max_time_coord = -1
        for coordinate_set in coordinate_sets:
            if isinstance(coordinate_set, list):
                time_coord_set = [x[2] for x in coordinate_set]
                if len(time_coord_set) > 0:
                    max_coord = max(time_coord_set)
                    max_time_coord = max([max_time_coord, max_coord])

        dif = max_time_coord - self.current_time_coordinate
        if dif >= 0:
            for i in range(dif + 1):

                if coord_patches_to_extend_set is not None:
                    sets = self.extend_data_qubits_to_current_time(coord_patches_to_extend_set)
                    if sets is not None:
                        # why should it be None?
                        self.configure_operation(*sets)

                        for key in patches_to_extend_set:
                            pc = self.layer_map.get_qubit_coordinate_2d(key)
                            orientation_integer = patches_state.get_patch_orientation_as_number(key)
                            self.coordinates[pc[0]][pc[1]][self.current_time_coordinate].sides_integer_value = orientation_integer


                # the last execution of this line
                # will automatically prepare the next gate application\
                # so do not call again...how to ensure this?
                # does it make sense to ensure it?
                self.increase_current_time_coordinate()


    def extend_data_qubits_to_current_time(self, coord_active_qubits, time_coord=None):
        sets = None
        span_set = []

        # new version
        for coord_data_qubit_2d in coord_active_qubits:
            # this is a temporary sets of instructions
            # consisting of operation type and everything needed for a single cell
            sets_tmp = self.create_use_data(coord_data_qubit_2d, time_coordinate=time_coord)
            if sets is None:
                # the temporary sets is transformed and span_set is separated
                # such that it can be updated if additional cells are to be added
                # see else branch of this if statement
                sets = sets_tmp
                span_set = sets[1]
            else:
                # once additional cells are added to this
                # then only the span_set is updated
                # this is a very shitty way of saying that the span sets should be merged
                span_set = span_set + sets_tmp[1]

        if sets is not None:
            sets_l = list(sets)
            sets_l[1] = span_set
            sets = tuple(sets_l)
            return sets

        return None

    def add_NOOP(self, si, sj):
        # add a new cell to the dictionary
        cell_id = self.add_cell_id(si, sj, len(self.coordinates[si][sj]))

        # add a new operation
        new_op = OperationDetails()
        new_op.spans.append(cell_id)

        op_id = self.add_op_id(new_op)

        # mark in the coordinates the op_id
        new_op_collection = OperationCollection(op_id)

        self.coordinates[si][sj].append(new_op_collection)

    def create_use_data(self, qubit_coord, time_coordinate=None):
        '''
        Creates a 3D cell instruction for using a patch (qubit) using 2D coordinates of the patch on the
        hardware arrangement of patches (map) and a time coordinate
        :param qubit_coord:
        :param time_coordinate:
        :return: the operation type, and the corresponding sets of representing the operation in 3D
        '''
        if time_coordinate is None:
            time_coordinate = self.current_time_coordinate
        return OperationTypes.USE_QUBIT, [(qubit_coord[0], qubit_coord[1], time_coordinate)], [], []

    def create_rotation(self, qubit):
        # requires two timesteps
        ancilla1 = self.layer_map.get_closest_ancillas(*qubit)[-1]
        ancilla2 = self.layer_map.get_closest_ancillas(*ancilla1)[-1]

        # add a new cell to the dictionary
        cell_1 = (*ancilla1, self.current_time_coordinate)
        cell_2 = (*ancilla2, self.current_time_coordinate)
        cell_3 = (*ancilla1, self.current_time_coordinate + 1)
        cell_4 = (*ancilla2, self.current_time_coordinate + 1)
        span_set = [cell_1, cell_2, cell_3, cell_4]

        touch_1 = (*qubit, self.current_time_coordinate)
        touch_2 = (*qubit, self.current_time_coordinate + 1)
        touch_set_data = [touch_1, touch_2]

        touch_set_meas = [cell_1, cell_3]

        return OperationTypes.USE_ANCILLA, span_set, touch_set_data, touch_set_meas

    def create_distillation(self):
        # assume a single distillation per layer
        # everything arranged in a contiguous area


        #first get the corner of the distillation
        corner = self.layer_map.get_distillation_corner()
        if corner == (-1, -1):
            print("ERROR: distillation corner not found!")

        span_set = []
        for qi in range(corner[0], corner[0] + self.layer_map.distillation_i_length):
            for qj in range(corner[1], corner[1] + self.layer_map.distillation_j_length):
                for ti in range(self.current_time_coordinate, self.current_time_coordinate + self.layer_map.distillation_t_length):
                    span_set.append((qi, qj, ti))

        touch_set_data = []
        touch_set_meas = []

        return OperationTypes.USE_DISTILLATION, span_set, touch_set_data, touch_set_meas


    def compute_qubits_for_s_gate(self, qub1_coord):
        # coordinates of the data qubit
        # qub1_coord = self.layer_map.circuit_qubits_to_patches[qubit]
        # qub1_coord = self.layer_map.get_qubit_coordinate_2d(qubit)

        """
            Which data patch closest to the current one should be moved?
        """
        qub2_coord = None
        take_next = True
        all_closest = self.layer_map.get_closest_data_qubits(*qub1_coord)
        idx_closest = 0

        set_of_ancillas = []
        direction_q = (0, 0)

        while take_next and (idx_closest < len(all_closest)):
            # Try until a good one is chosen
            while take_next and (idx_closest < len(all_closest)):
                qub2_coord = all_closest[idx_closest]
                idx_closest += 1

                """
                    A patch should be away from the boundaries of the checker board
                """
                part2_d = (
                abs(qub2_coord[0] - self.layer_map.dimension_i), abs(qub2_coord[1] - self.layer_map.dimension_j))
                dist_sequence = qub2_coord + part2_d

                # Assume everything is OK
                take_next = False
                for x in dist_sequence:
                    # the neighbour patch is not away from the boundary of the board
                    if x < 1:
                        take_next = True

            # There is something wrong here
            if take_next and idx_closest == len(all_closest):
                print("ERROR! No patch to take and to move for the S gate to work")

            # compute direction of qub1 qub2
            direction_q = (qub1_coord[0] - qub2_coord[0], qub1_coord[1] - qub2_coord[1])

            # there are two perpendicular directions of direction_q
            directions_p = [
                (1 - abs(direction_q[0]), 1 - abs(direction_q[1])),
                (abs(direction_q[0]) - 1, abs(direction_q[1]) - 1)
            ]

            set_of_ancillas = self.layer_map.get_closest_ancillas(*qub1_coord, directions_p)
            how_many_ancilla_in_here = len(set_of_ancillas)
            if how_many_ancilla_in_here == 0:
                take_next = True

        anc1_coord = set_of_ancillas[0]

        # along direction of qub1 qub2 find ancilla2
        anc2_coord = (anc1_coord[0] - direction_q[0], anc1_coord[1] - direction_q[1])

        # along direction of qub1 qub2 find ancilla3
        anc3_coord = (anc2_coord[0] - direction_q[0], anc2_coord[1] - direction_q[1])

        return qub1_coord, qub2_coord, anc1_coord, anc2_coord, anc3_coord

    def compute_qubits_for_s_gate_ancilla(self, qub1_coord):
        # coordinates of the data qubit
        # nothing needs to be moved
        # because I assume layout one is always used and the ancilla is on the double channel
        # TODO: Hardcoded computation of the coordinates - make it more beautiful in the future
        qub2_coord = (qub1_coord[0] - 1, qub1_coord[1] + 0)
        anc1_coord = (qub1_coord[0] + 0, qub1_coord[1] + 1)
        anc2_coord = (qub1_coord[0] - 1, qub1_coord[1] + 1)

        return qub1_coord, qub2_coord, anc1_coord, anc2_coord, (-1, -1)

    def find_name_for_qubit_coordinate(self, coordinate):
        '''
           This is a complicated way to find the name of the qubit that is at a certain coordinate
           First: if it is ancilla -> then it should not be filtered out, because it did not exist in the first place?
           Second: if it is data qubit -> is it tracked? -> it has a name, and it is tracked
           Third: if it is not data qubit, and not tracked -> it has a name, and it is not tracked
       '''
        # no name...is default
        name = ""

        # if it is not a qubit on the map, then return no_name
        if self.layer_map.placement_map[coordinate[0]][coordinate[1]] != lll.MapCellType.QUBIT:
            return name

        # at this stage it is a data qubit
        # check in the

        coordinate_2d = (coordinate[0], coordinate[1])
        for key in self.layer_map.circuit_qubits_to_patches:
            if self.layer_map.circuit_qubits_to_patches[key] == coordinate_2d:
                # found the name
                name = key

        # otherwise it is not a circuit qubit, but just a data patch which is not used and not tracked
        # TODO: hope this is correct

        return name

    def create_s_gate(self, qub_command_string, patches_state, active_patches):
        '''
        Implementation of an S gate
        :param qub_string:
        :return: nothing
        '''

        qub_string = self.layer_map.get_circuit_qubit_name(qub_command_string)
        qub1_coord = self.layer_map.get_qubit_coordinate_2d(qub_string)

        if qub_string == 'ANCILLA':
            qub1_coord, qub2_coord, anc1_coord, anc2_coord, anc3_coord = self.compute_qubits_for_s_gate_ancilla(qub1_coord)
        else:
            qub1_coord, qub2_coord, anc1_coord, anc2_coord, anc3_coord = self.compute_qubits_for_s_gate(qub1_coord)

        qub2_name = self.find_name_for_qubit_coordinate(qub2_coord)
        anc3_name = self.find_name_for_qubit_coordinate(anc3_coord)

        tmp_active_patches = [x for x in active_patches]

        #
        # qub2_coord is moved to another ancilla
        # this is a data qubit which occupies space required for implementing the S gate
        # A. it can happen that qub2_coord is actually not used by the computation
        # -> in that case, do not move it
        # B. it can also happen, that the S gate is applied on the ANCILLA patch
        # -> also no need to move anything, because in the current hard coded setup
        #   there is enough space for the S gate
        #
        if qub_string != 'ANCILLA' and (qub2_name in active_patches):
            #
            # create data movement to ancilla
            #
            span_set = [qub2_coord + (self.current_time_coordinate, )
                , anc2_coord + (self.current_time_coordinate, )
                , anc3_coord + (self.current_time_coordinate, )]

            sets = (OperationTypes.MOVE_PATCH, span_set, [], [])
            self.configure_operation(*sets)

            # filter the qubit that is moved
            tmp_active_patches = [x for x in tmp_active_patches if x != qub2_name]
            self.move_current_time_coordinate_to_max_from_coordinates(sets, patches_state, tmp_active_patches)
            # add the destination
            if anc3_name != "":
                # different from noname
                tmp_active_patches.append(anc3_name)

        #
        # create S gate
        #
        span_set = [
            qub1_coord + (self.current_time_coordinate,)
            , qub2_coord + (self.current_time_coordinate,)
            , anc1_coord + (self.current_time_coordinate,)
            , anc2_coord + (self.current_time_coordinate,)
            , qub1_coord + (self.current_time_coordinate + 1,)
            , qub2_coord + (self.current_time_coordinate + 1,)
            , anc1_coord + (self.current_time_coordinate + 1,)
            , anc2_coord + (self.current_time_coordinate + 1,)
        ]

        sets = (OperationTypes.USE_S_GATE, span_set, [], [])
        self.configure_operation(*sets)

        # filter the current qubit from the set of things to update
        tmp_active_patches = [x for x in tmp_active_patches if x != qub_string]
        self.move_current_time_coordinate_to_max_from_coordinates(sets, patches_state, tmp_active_patches)
        # put it back
        tmp_active_patches.append(qub_string)


        #
        # Move back
        #

        if qub_string != 'ANCILLA' and (qub2_name in active_patches):
            #
            # create data movement to ancilla
            #
            span_set = [qub2_coord + (self.current_time_coordinate,)
                , anc2_coord + (self.current_time_coordinate,)
                , anc3_coord + (self.current_time_coordinate,)]

            sets = (OperationTypes.MOVE_PATCH, span_set, [], [])
            self.configure_operation(*sets)

            # filter the qubit that is moved
            tmp_active_patches = [x for x in tmp_active_patches if x != anc3_name]
            self.move_current_time_coordinate_to_max_from_coordinates(sets, patches_state, tmp_active_patches)
            # add the destination
            if qub2_name != "":
                tmp_active_patches.append(qub2_name)


    def get_ancilla_based_on_operator_orientation(self, qubit_name, patches_state, touchsides):
        """
        I am assuming setup_arrangement_one from layer_map is default and only used
        If XOrientation is Original:
            -> X boundary is on positive-y and negative-y (py and ny)
            -> Z boundary is on positive-x and negative-x (px and nx)

        If XOrientation is Rotated:
            -> the above, but with inversed meanings
        """
        x_directions = [(0, 1), [0, -1]]
        z_directions = [(1, 0), [-1, 0]]

        # What is needed?
        ancilla_qub = []
        coord_qubit = self.layer_map.get_qubit_coordinate_2d(qubit_name)

        if touchsides == "X":
            # I need X. Where is it?
            if patches_state.per_patch_x_orientation[qubit_name] == ps.XOrientation.ORIGINAL:
                ancilla_qub = self.layer_map.get_closest_ancillas(coord_qubit[0], coord_qubit[1], z_directions)
            else:
                ancilla_qub = self.layer_map.get_closest_ancillas(coord_qubit[0], coord_qubit[1], x_directions)
        else:
            # I need Z. Where is it? -> Flip the direction interpretation
            if patches_state.per_patch_x_orientation[qubit_name] == ps.XOrientation.ORIGINAL:
                ancilla_qub = self.layer_map.get_closest_ancillas(coord_qubit[0], coord_qubit[1], z_directions)
            else:
                ancilla_qub = self.layer_map.get_closest_ancillas(coord_qubit[0], coord_qubit[1], x_directions)

        return ancilla_qub

    def create_route_between_qubits(self, qubits_list, patches_state, touchsides = ["X", "X"]):
        '''
        Constructs the necessary commands between two qubits
        :param qubits_list: a list of (two, for the moment) qubit string names to connect
        :param patches_state: object that tracks the X orientation of patch boundaries
        :param touchsides: on which sides of the patch should the qubits be touched?
        :return: instruction set
        '''

        span_set = []
        #
        # These are the data qubits assumed to be measured by a multibody measurement
        #
        touch_set_data = []
        #
        # The multibody measurement is an object which
        # which contains cells that touch 1:1 mapping the ones from touch_set_data
        #
        touch_set_meas = []

        # If this is the first part of a longer multibody measurement
        first_sub_chain = True
        for qubit_list_idx in range(len(qubits_list) - 1):

            qubit_name_1 = self.layer_map.get_circuit_qubit_name(qubits_list[qubit_list_idx])
            qubit_name_2 = self.layer_map.get_circuit_qubit_name(qubits_list[qubit_list_idx + 1])

            ancilla_qub1 = self.get_ancilla_based_on_operator_orientation(qubit_name_1, patches_state, touchsides[qubit_list_idx])
            ancilla_qub2 = self.get_ancilla_based_on_operator_orientation(qubit_name_2, patches_state, touchsides[qubit_list_idx + 1])

            if (len(ancilla_qub1) == 0) or (len(ancilla_qub2) == 0):
                print("ERROR! one of the qubits needed to be rotated first! Could not touch its correct boundary!")

            #
            # Here it is OK to build a tuple
            # The ancillas exist and can be used
            #
            qubit_tuple = (ancilla_qub1[0], ancilla_qub2[0])
            route = self.layer_map.get_route_between_qubits(*qubit_tuple)

            # take the 2D coordinates and create 3D coordinates using the current_time_coordinate
            for cell in route:
                n_coord = (*cell, self.current_time_coordinate)
                if n_coord not in span_set:
                    span_set.append(n_coord)

            coord_qub1 = self.layer_map.get_qubit_coordinate_2d(qubit_name_1)
            coord_qub2 = self.layer_map.get_qubit_coordinate_2d(qubit_name_2)
            if len(route) == 0:
                #
                # The span_set is empty and it means that the data patches are next to another?
                # TODO: I am not sure if this is correct, or if it makes sense. Should not get into this scenario...
                #
                # touch_set_data.append((*coord_qub1, self.current_time_coordinate))
                # touch_set_meas.append((*coord_qub2, self.current_time_coordinate))
                print("ERROR! Zero length path between two nodes which should have been separate!")
            if len(route) == 1:
                if first_sub_chain:
                    touch_set_data.append((*coord_qub1, self.current_time_coordinate))
                touch_set_data.append((*coord_qub2, self.current_time_coordinate))
                # touch_set_data[0] is measured by the first one in the route sequence
                if first_sub_chain:
                    touch_set_meas.append(span_set[0])
                # ouch_set_data[1] is measured by the last one in the route sequence
                touch_set_meas.append(span_set[0])
            else:
                if first_sub_chain:
                    touch_set_data.append((*coord_qub1, self.current_time_coordinate))
                touch_set_data.append((*coord_qub2, self.current_time_coordinate))
                # touch_set_data[0] is measured by the first one in the route sequence
                if first_sub_chain:
                    touch_set_meas.append(span_set[0])
                # ouch_set_data[1] is measured by the last one in the route sequence
                touch_set_meas.append(span_set[-1])

            first_sub_chain = False

        return OperationTypes.USE_ANCILLA, span_set, touch_set_data, touch_set_meas

    def configure_operation(self, op_type, span_set, touch_set_data, touch_set_meas):
        """
        Configures the 3D cells in the cube for the specified operation
        :param op_type:
        :param span_set:
        :param touch_set_data:
        :param touch_set_meas:
        :return: number of steps the operation increased the time coordinate with
        """
        # how many times does the operation need to be moved along the time axis?
        nr_time_increases = self.accommodate_object(span_set)

        # update the coordinate sets with the new time coordinate?
        span_set = self.update_coordinate_set_from_time_delta(span_set, nr_time_increases)
        touch_set_data = self.update_coordinate_set_from_time_delta(touch_set_data, nr_time_increases)
        touch_set_meas = self.update_coordinate_set_from_time_delta(touch_set_meas, nr_time_increases)

        # add the coordinates, if they do not exist

        # create the index sets instead of coordinate sets
        span_set_idx = self.transform_coordinate_set_into_index_set(span_set)

        if len(touch_set_data) != len(touch_set_meas):
            print("ERROR: Touch sets do not have same length")
        touch_idx = {}
        for i in range(len(touch_set_data)):
            idx1 = self.get_cell_id(*touch_set_data[i])
            idx2 = self.get_cell_id(*touch_set_meas[i])
            # the patch indexed by idx1 is a data patch which is measured
            # by the patch indexed by idx2 which is an ancilla patch
            #
            # effectively, this says that
            # cell idx should have a directed edge (in a potential graph visualisation) with cell idx2
            #
            touch_idx[idx1] = idx2

        # the data qubit where it touches should already exist
        # but their op type is NOOP
        # change it to whatever may be needed, depending on the map
        for qubit in touch_set_data:
            # idx = self.get_cell_id(*qubit)
            # op_id = self.coordinates[qubit[0]][qubit[1]][qubit[2]]
            # if self.operations_dictionary[op_id].op_type == OperationTypes.NOOP:
            if self.coordinates[qubit[0]][qubit[1]][qubit[2]].has_single_noop(self.operations_dictionary):
                # take the type from the layer_map
                self.debug_cell(qubit[0], qubit[1], qubit[2])

        for qubit in touch_set_meas:
            # idx = self.get_cell_id(*qubit)
            # op_id = self.coordinates[qubit[0]][qubit[1]][qubit[2]]
            # if self.operations_dictionary[op_id].op_type == OperationTypes.NOOP:
            if self.coordinates[qubit[0]][qubit[1]][qubit[2]].has_single_noop(self.operations_dictionary):
                # take the type from the layer_map
                self.debug_cell(qubit[0], qubit[1], qubit[2])

        # add a new operation
        # new_op = {"op_type": op_type,
        #           "spans": span_set_idx,
        #           "touches": touch_idx,
        #           "decorator": OperationTypes.NOOP}

        # this is the new operation in the collection of operations
        new_op = OperationDetails()
        new_op.op_type = op_type
        new_op.spans = span_set_idx
        new_op.touches = touch_idx

        op_id = self.add_op_id(new_op)

        # mark in the coordinates the op_id
        for coord in span_set:

            ops_collection = self.coordinates[coord[0]][coord[1]][coord[2]]

            # I assume this cell has a single NOOP, which will not be used anymore
            # I can remove it from the dictionary of operations
            if ops_collection.has_single_noop(self.operations_dictionary):
                # get the old id
                old_op_id = ops_collection.get_first_op_id()
                # replace it with the new id
                ops_collection.replace_single_noop_with_other(op_id)
                # remove the old id from the operations dictionary
                self.remove_op_id(old_op_id)

                #self.coordinates[coord[0]][coord[1]][coord[2]] = op_id
            else:
                # something is wrong?
                # should it be possible to add an operation if the cell is not NOOP?
                # print("ERROR???! Cell is not NOOP for configure_operation")
                ops_collection.append_operation(op_id)

        return nr_time_increases

    def accommodate_hardware_sizes(self, mi, mj):
        '''
        Always assume that at each time step the arrays have the same dimensions
        :param mi: maximum i
        :param mj: maximum j
        :return: nothing
        '''

        # add missing rows
        dif_i = mi - self.get_isize()
        for ri in range(dif_i):
            self.coordinates.append([])

        for si in range(self.get_isize()):
            # add missing columns
            # it is not guaranteed, at this point, that len is equal for all rows
            dif_j = mj - len(self.coordinates[si])
            for rj in range(dif_j):
                self.coordinates[si].append([])

        mt = self.get_tsize()
        for si in range(self.get_isize()):
            for sj in range(self.get_jsize()):
                dif_t = mt - len(self.coordinates[si][sj])
                for rt in range(dif_t):
                    self.add_NOOP(si, sj)


    def place_random(self, mt):
        """
        Was used for random testing of placement
        :param mt:
        :return:
        """
        # add time steps
        for rt in range(mt - self.get_tsize()):
            self.add_time_coordinate()

        # iterate over the entire cuboid and
        # randomly select type of local cell operation
        for i in range(self.get_isize()):
            for j in range(self.get_jsize()):
                for t in range(self.get_tsize()):
                    random_i = random.randint(0, 1)
                    op_type = OperationTypes.NOOP

                    # what is this coordinate in the logical layout?
                    map_entry = self.layer_map.placement_map[i][j]
                    if map_entry == lll.MapCellType.ANCILLA:
                        if random_i == 1:
                            op_type = OperationTypes.USE_ANCILLA
                    elif map_entry == lll.MapCellType.QUBIT:
                        if random_i == 1:
                            op_type = OperationTypes.USE_QUBIT
                    elif map_entry == lll.MapCellType.DISTILLATION:
                            #if random_i == 1:
                                op_type = OperationTypes.USE_DISTILLATION

                    op_id = self.coordinates[i][j][t]
                    self.operations_dictionary[op_id]["op_type"] = op_type

    def place_manual(self):
        """
        Was used for manual testing of placements
        :return:
        """
        sets = self.create_distillation()
        self.configure_operation(*sets)

        qub = self.layer_map.get_potential_data_patches_coordinates_2d()[0]
        sets = self.create_rotation(qubit=qub)
        self.configure_operation(*sets)

        qub = self.layer_map.get_potential_data_patches_coordinates_2d()[4]
        sets = self.create_rotation(qubit=qub)
        self.configure_operation(*sets)

    def debug_cell(self, i, j, t):
        """
        Marks a cell at a given 3D coordinate by its type from the layer map
        :param i:
        :param j:
        :param t:
        :return: Nothing
        """
        op_t = OperationTypes.NOOP
        xxx = self.layer_map.placement_map[i][j]
        if xxx == lll.MapCellType.QUBIT:
            op_t = OperationTypes.USE_QUBIT
        elif xxx == lll.MapCellType.ANCILLA:
            op_t = OperationTypes.USE_ANCILLA
        elif xxx == lll.MapCellType.DISTILLATION:
            op_t = OperationTypes.USE_DISTILLATION

        op_id = self.coordinates[i][j][t].operations[0]
        self.operations_dictionary[op_id].op_type = op_t

    def debug_layer_map(self):
        """
        At time coordinate zero, all the cells are marked by their type
        :return: Nothing
        """
        for i in range(self.get_isize()):
            for j in range(self.get_jsize()):
                self.debug_cell(i, j, 0)

    def debug_all_paths(self):
        # each path is drawn in a separate layer\
        # layers are separated by an empty one in between to ease visualisation
        for qubit_tuple in self.layer_map.routes:
            print("debug path:", qubit_tuple)

            # first time increment
            self.increase_current_time_coordinate()

            # and this is the route
            sets = self.create_route_between_qubits(qubit_tuple)
            self.configure_operation(*sets)

            # the cell where the route starts
            coord_1 = self.layer_map.circuit_qubits_to_patches[qubit_tuple[0]]
            self.debug_cell(*coord_1, self.current_time_coordinate)

            # the cell where the route ends
            coord_2 = self.layer_map.circuit_qubits_to_patches[qubit_tuple[1]]
            self.debug_cell(*coord_2, self.current_time_coordinate)

            # last time increment
            self.increase_current_time_coordinate()


