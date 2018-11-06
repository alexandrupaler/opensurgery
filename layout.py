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


class OperationTypes(Enum):
    NOOP = 0
    USE_QUBIT = 1  # measures stabilisers in the patch of loqical qubit
    USE_ANCILLA = 3
    USE_DISTILLATION = 7
    ######################
    ROTATE_QUBIT = 2 #ancilla qubits are not rotated (at least in this scheme) and therefore this is not applicable to them

class PlacementStatus(Enum):
    OK = 0
    NO_TIME = 1
    ALREADY_BUSY = 3
    NO_SPACE = 5


class CubeLayout:
    def __init__(self, lll_map):
        print("layout")

        self.layer_map = lll_map

        # default array is 0,0,1 in time with default op
        self.coordinates = [[[0]]]

        # the default operation is null - nothing
        self.operations_dictionary = {0: {"op_type": OperationTypes.NOOP, "spans": [0], "touches": {}}}

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
        new_id = len(self.operations_dictionary) + 1
        self.operations_dictionary[new_id] = new_op
        return new_id

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

    def check_coordinate_span_set(self, span_set, time_offset):
        for coord in span_set:
            # check if time coordinate is ok
            if coord[2] + time_offset >= self.get_tsize():
                # problem - it goes outside of the available time
                return PlacementStatus.NO_TIME

            if (coord[0] >= self.get_isize()) or (coord[1] >= self.get_jsize()):
                # problem - it goes outside of the available space
                print("here ->", coord)
                return PlacementStatus.NO_SPACE

            operation_id = self.coordinates[coord[0]][coord[1]][coord[2] + time_offset]
            operation = self.operations_dictionary[operation_id]

            if operation["op_type"] != OperationTypes.NOOP:
                # there is something different at this coordinate
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

    def move_current_time_coordinate_to_max_from_set(self, coordinate_sets):
        for coordinate_set in coordinate_sets:
            if isinstance(coordinate_set, list):
                time_coord_set = [x[2] for x in coordinate_set]
                if len(time_coord_set) > 0:
                    max_coord = max(time_coord_set)
                    self.current_time_coordinate = max_coord

    def extend_data_qubits_to_current_time(self):
        for data_qubit in self.layer_map.circuit_qubits_to_patches:
            if data_qubit not in ["A", "ANCILLA"]:
                sets = self.create_use_data(self.layer_map.circuit_qubits_to_patches[data_qubit])
                self.configure_operation(*sets)

    def add_NOOP(self, si, sj):
        # add a new cell to the dictionary
        cell_id = self.add_cell_id(si, sj, len(self.coordinates[si][sj]))

        # add a new operation
        new_op = {"op_type": OperationTypes.NOOP, "spans": [cell_id], "touches": {}}
        op_id = self.add_op_id(new_op)

        # mark in the coordinates the op_id
        self.coordinates[si][sj].append(op_id)

    def create_use_data(self, qubit):
        return OperationTypes.USE_QUBIT, [(qubit[0], qubit[1], self.current_time_coordinate)], [], []

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

    def create_ancilla_route(self, qubit_tuple_in):
        try:
            x = int(qubit_tuple_in[0])
        except:
            x = qubit_tuple_in[0]

        try:
            y = int(qubit_tuple_in[1])
        except:
            y = qubit_tuple_in[1]

        qubit_tuple = (x, y)

        span_set = []
        route = self.layer_map.get_route_between_qubits(*qubit_tuple)
        if route is not None:
            for cell in route:
                span_set.append((*cell, self.current_time_coordinate))

        touch_set_data = []
        coord_1 = self.layer_map.circuit_qubits_to_patches[qubit_tuple[0]]
        touch_set_data.append((*coord_1, self.current_time_coordinate))
        coord_2 = self.layer_map.circuit_qubits_to_patches[qubit_tuple[1]]
        touch_set_data.append((*coord_2, self.current_time_coordinate))

        touch_set_meas = []
        if len(span_set) > 0:
            touch_set_meas.append(span_set[0])
            touch_set_meas.append(span_set[-1])
        else:
            #the span_set is empty and it means that the data patches are next to another?
            touch_set_meas.append(touch_set_data[1])
            touch_set_data.remove(touch_set_data[1])

        return OperationTypes.USE_ANCILLA, span_set, touch_set_data, touch_set_meas

    def configure_operation(self, op_type, span_set, touch_set_data, touch_set_meas):
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
            touch_idx[idx1] = idx2

        # the data qubit where it touches should already exist
        # but their op type is NOOP
        # change it to USE_QUBIT
        for qubit in touch_set_data:
            idx = self.get_cell_id(*qubit)
            op_id = self.coordinates[qubit[0]][qubit[1]][qubit[2]]
            if self.operations_dictionary[op_id]["op_type"] == OperationTypes.NOOP:
                # take the type from the layer_map
                if self.layer_map.placement_map[qubit[0]][qubit[1]] == lll.MapCellType.ANCILLA:
                    self.operations_dictionary[op_id]["op_type"] = OperationTypes.USE_ANCILLA
                elif self.layer_map.placement_map[qubit[0]][qubit[1]] == lll.MapCellType.QUBIT:
                    self.operations_dictionary[op_id]["op_type"] = OperationTypes.USE_QUBIT
                elif self.layer_map.placement_map[qubit[0]][qubit[1]] == lll.MapCellType.DISTILLATION:
                    self.operations_dictionary[op_id]["op_type"] = OperationTypes.USE_DISTILLATION

        # add a new operation
        new_op = {"op_type": op_type,
                  "spans": span_set_idx,
                  "touches": touch_idx}

        # this is the new operation in the collection of operations
        op_id = self.add_op_id(new_op)

        # mark in the coordinates the op_id
        for coord in span_set:
            self.coordinates[coord[0]][coord[1]][coord[2]] = op_id



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


    '''
    Din cauza dictionarului as putea sa renunt la arrayul de coordonate?
    Deocamdata nu, am inceput asa si pare a fi ok
    '''

    def place_random(self, mt):
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
        sets = self.create_distillation()
        self.configure_operation(*sets)

        qub = self.layer_map.get_data_qubits()[0]
        sets = self.create_rotation(qubit=qub)
        self.configure_operation(*sets)

        qub = self.layer_map.get_data_qubits()[4]
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

        op_id = self.coordinates[i][j][t]
        self.operations_dictionary[op_id]["op_type"] = op_t

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
            sets = self.create_ancilla_route(qubit_tuple)
            self.configure_operation(*sets)

            # the cell where the route starts
            coord_1 = self.layer_map.circuit_qubits_to_patches[qubit_tuple[0]]
            self.debug_cell(*coord_1, self.current_time_coordinate)

            # the cell where the route ends
            coord_2 = self.layer_map.circuit_qubits_to_patches[qubit_tuple[1]]
            self.debug_cell(*coord_2, self.current_time_coordinate)

            # last time increment
            self.increase_current_time_coordinate()


