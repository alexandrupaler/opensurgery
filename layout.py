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
import logical_layout as lll


class OperationTypes(Enum):
    DEFAULT = 0
    USE_QUBIT = 1  # measures stabilisers in the patch of loqical qubit
    USE_ANCILLA = 3
    USE_DISTILLATION = 7
    ######################
    ROTATE_QUBIT = 2



class CubeLayout:
    def __init__(self, lll_map):
        print("layout")

        self.layer_map = lll_map

        # default array is 0,0,1 in time with default op
        self.coordinates = [[[0]]]

        # the default operation is null - nothing
        self.operations_dictionary = {0: {"op_type": OperationTypes.DEFAULT, "spans": [0], "touches": {}}}

        # default setup: cell 0,0,0 has id 0
        self.cell_dictionary = {(0, 0, 0): 0}

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
        new_id = len(self.cell_dictionary) + 1

        # self.cell_dictionary[new_id] = (si, sj, st)
        self.cell_dictionary[(si, sj, st)] = new_id

        return new_id

    def add_op_id(self, new_op):
        new_id = len(self.operations_dictionary) + 1
        self.operations_dictionary[new_id] = new_op
        return new_id

    def add_NOOP(self, si, sj):
        # add a new cell to the dictionary
        cell_id = self.add_cell_id(si, sj, len(self.coordinates[si][sj]))

        # add a new operation
        new_op = {"op_type": OperationTypes.DEFAULT, "spans": [cell_id], "touches": {}}
        op_id = self.add_op_id(new_op)

        # mark in the coordinates the op_id
        self.coordinates[si][sj].append(op_id)

    def add_time_coordinate(self):
        '''
        Inefficient way of adding another time slice
        :return: nothing
        '''
        for si in range(self.get_isize()):
            for sj in range(self.get_jsize()):
                self.add_NOOP(si, sj)

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

    def random_elements(self, mt):
        # add time steps
        for rt in range(mt - self.get_tsize()):
            self.add_time_coordinate()

        # iterate over the entire cuboid and
        # randomly select type of local cell operation
        for i in range(self.get_isize()):
            for j in range(self.get_jsize()):
                for t in range(self.get_tsize()):
                    random_i = random.randint(0, 1)
                    op_type = OperationTypes.DEFAULT

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
