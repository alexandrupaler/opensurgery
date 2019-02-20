from enum import Enum
import math
import networkx as nx

class MapCellType(Enum):
    QUBIT = 3
    ANCILLA = 5
    DISTILLATION = 7

class LayerMap:
    def __init__(self):
        # two-dimensional array storing the type of the cells using MapCellType
        self.placement_map = []

        # initial dimensions are -1 and -1
        self.dimension_i = -1
        self.dimension_j = -1

        # hard coded dimensions of the distillation
        self.distillation_i_length = 4
        self.distillation_j_length = 8
        self.distillation_t_length = 10

        # ancilla coordinate will be changed when the placement_one method is called
        self.circuit_qubits_to_patches = {'A': (3, 0), 'ANCILLA': (4, 0)}

        # collection of routes between pairs of ancilla patches
        # indexed by tuples formed of ancilla patch 2D coordinates
        self.routes = {}

    def compute_routes_between_qubits(self):
        '''
            Compute for all ancilla patche pairs the routes between them
            Previous version used to compute between the data patches
            But this is not OK, because it depends on which boundary
            of the data patch one wants to merge and split
        :return: nothing
        '''

        ancilla_patch_coordinates_2d = self.get_potential_ancilla_patches_coordinates_2d()

        # begin version two with networkx
        grid_graph = nx.grid_2d_graph(self.dimension_i, self.dimension_j)
        for qi in range(self.dimension_i):
            for qj in range(self.dimension_j):
                # consider only ANCILLA patches
                coord_ancilla = (qi, qj)
                if coord_ancilla not in ancilla_patch_coordinates_2d:
                    # if it is not ancilla, remove it
                    grid_graph.remove_node((qi, qj))
        # end new version

        #
        # Compute routes between pairs of ancilla coordinates
        #
        for coord_ancilla1 in ancilla_patch_coordinates_2d:
            for coord_ancilla2 in ancilla_patch_coordinates_2d:

                # skip routes between the same cell?
                # maybe this should not be skipped
                if coord_ancilla1 == coord_ancilla2:
                    continue

                # if no route was stored by now
                if self.get_route_between_qubits(coord_ancilla1, coord_ancilla2) is None:
                    # version two with networkx
                    back_path = nx.astar_path(grid_graph, coord_ancilla1, coord_ancilla2)
                    # end version two

                    # store the paths, if something was found
                    if len(back_path) > 0:
                        #
                        # the key is a tuple of coordinates (which are tuples)
                        #
                        self.routes[(coord_ancilla1, coord_ancilla2)] = list(back_path)
                        # store the inverse path, too -- redundant, but simpler to code
                        self.routes[(coord_ancilla2, coord_ancilla1)] = list(reversed(back_path))

    def get_route_between_qubits(self, ancilla1, ancilla2):
        '''
        Returns a path spanned between two ancilla patch coordinates
        :param ancilla1: 2D coordinate of first ancilla
        :param ancilla2: 2D coordinate of second ancilla
        :return: a list of ancilla 2D coordinates over which the path runs
        '''
        patch_tuple_a = (ancilla1, ancilla2)
        if patch_tuple_a in self.routes:
            return self.routes[patch_tuple_a]

        # patch_tuple_b = (ancilla2, ancilla1)
        # if patch_tuple_b in self.routes:
        #     return list(reversed(self.routes[patch_tuple_b]))

        # there is no path computed between the two patches
        return None

    def get_circuit_qubit_name(self, index):
        '''
            Generates the name of circuit qubits
            It will be used in the circuit_qubits_to_patches map
            This is to have nice, readable keys
        :param index: number of the qubit
        :return: string name of the qubit
        '''
        #
        # It could happen that in a strange situation
        # the name for ANCILLA or A will have to be computed
        #
        if isinstance(index, str) and ((index == "ANCILLA") or (index == "A")):
            return index
        # Assume it is an int (even as string) and that it should work
        # Otherwise...problem
        return "circuit_" + str(index)

    def map_circuit_qubits_to_patches(self, list_of_qubit_indices):
        '''
            Associates qubit names computed from a list of indices
            to 2D coordinates on the placement map
        :param list_of_qubit_indices: list of qubit indices from the circuit to be mapped
        :return: nothing
        '''
        all_data_qubit_coords = self.get_potential_data_patches_coordinates_2d()

        for qubit_index in list_of_qubit_indices:
            qubit_name = self.get_circuit_qubit_name(qubit_index)
            self.circuit_qubits_to_patches[qubit_name] = all_data_qubit_coords[qubit_index]

            print("qubit", qubit_name, "@", all_data_qubit_coords[qubit_index])

    def get_qubit_coordinate_2d(self, qubit_string_name):
        '''

        :return: 2D coordinate of circuit qubit, the ANCILLA, or the A qubit
        '''
        if qubit_string_name == "ANCILLA":
            return self.circuit_qubits_to_patches["ANCILLA"]
        elif qubit_string_name == "A":
            return self.circuit_qubits_to_patches["A"]

        # qubit_index = int(qubit_string_name)
        # qubit_name = self.get_circuit_qubit_name(qubit_index)
        return self.circuit_qubits_to_patches[qubit_string_name]

    def setup_arrangement_one(self, nr_logical_qubits, patches_to_track):
        '''
            Setups a grid layout similar to the one from Austin's paper

        :param nr_logical_qubits: how many of the data patches are required for circuit qubits
        :param patches_to_track: a PatchesState object to track the active data patches
        :return: nothing
        '''

        # total patches
        nr_data_patches_per_line = self.distillation_j_length - 2 # two because of ancilla
        nr_data_lines = math.ceil(nr_logical_qubits / nr_data_patches_per_line)
        nr_non_distillation_lines = 2 * nr_data_lines

        # the arrangement has the width of a distillation
        self.dimension_j = self.distillation_j_length
        self.dimension_i = nr_non_distillation_lines + self.distillation_i_length

        # for the beginning everything is ancilla
        for i in range(self.dimension_i):
            self.placement_map.append([])
            for j in range(self.dimension_j):
                self.placement_map[i].append(MapCellType.ANCILLA)

        #
        #   Place the qubit and ancilla patches on the map
        #
        for i in range(self.dimension_i):
            # default cell type on a row is qubit
            map_type = MapCellType.QUBIT
            # on each middle row from three, the type is ancilla
            if (i % 3) == 1:
                map_type = MapCellType.ANCILLA
            # set the row cell types
            for j in range(self.dimension_j):
                self.placement_map[i][j] = map_type

        # in the middle of each row two ancilla patches are placed one next to the other
        for i in range(self.dimension_i):
            self.placement_map[i][self.dimension_j // 2] = MapCellType.ANCILLA
            self.placement_map[i][self.dimension_j // 2 - 1] = MapCellType.ANCILLA

        #
        # The ancilla is on the middle channel
        #
        # self.circuit_qubits_to_patches['ANCILLA'] = (4, self.dimension_j // 2 - 1)
        # On the last line in the middle channel
        self.circuit_qubits_to_patches['ANCILLA'] = (self.dimension_i - 1, self.dimension_j // 2 - 1)

        #
        # Place distillation cells
        #
        for i in range(self.distillation_i_length):
            for j in range(self.distillation_j_length):
                self.placement_map[i][j] = MapCellType.DISTILLATION

        #
        # Map the logical qubits to data patches
        #
        logical_qubit_indices = list(range(nr_logical_qubits))
        self.map_circuit_qubits_to_patches(logical_qubit_indices)

        #
        # Add the circuit qubit patches which need to be tracked in the layouting part
        #
        for cq_index in logical_qubit_indices:
            cq_name = self.get_circuit_qubit_name(cq_index)
            patches_to_track.add_active_patch(cq_name)

        #
        # compute the distances between the ancilla patches
        #
        self.compute_routes_between_qubits()


    def get_closest_ancillas(self, qub_i, qub_j, search_directions = None):
        '''
        Gets the closest ancilla next to a data qubit specified as i,j coordinates
        :param qubit: start qubit 2D coordinates
        :return: tuple of 2D coordinates, or (-1, -1) if something went wrong
        '''
        ancillas = []

        if (qub_i, qub_j) == self.circuit_qubits_to_patches["A"]:
            ancillas.append((3, 1))

        directions = []
        if search_directions is None:
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        else:
            directions = search_directions

        # search in the immediate neighbourhood
        for qt in directions:
            n_q1 = qub_i + qt[0]
            n_q2 = qub_j + qt[1]

            # negative indices are dangerous in python
            if (n_q1 < 0) or (n_q2 < 0) or (n_q1 >= self.dimension_i) or (n_q2 >= self.dimension_j):
                continue

            n_cell_type = self.placement_map[n_q1][n_q2]

            if n_cell_type == MapCellType.ANCILLA:
                ancillas.append((n_q1, n_q2))

        return ancillas

    def get_closest_data_qubits(self, qub_i, qub_j, search_directions = None):
        '''
        Gets the closest data qubit next to a qubit specified as i,j coordinates
        :param qubit: start qubit 2D coordinates
        :return: tuple of 2D coordinates, or (-1, -1) if something went wrong
        '''
        qubits = []

        directions = []
        if search_directions is None:
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        else:
            directions = search_directions

        # search in the immediate neighbourhood
        for qt in directions:
            n_q1 = qub_i + qt[0]
            n_q2 = qub_j + qt[1]

            # negative indices are dangerous in python
            if n_q1 < 0 or n_q2 < 0 or n_q1 >= self.dimension_i or n_q2 >= self.dimension_j:
                continue

            n_cell_type = self.placement_map[n_q1][n_q2]

            if n_cell_type == MapCellType.QUBIT:
                # ancilla = (n_q1, n_q2)
                qubits.append((n_q1, n_q2))

        return qubits

    def get_distillation_corner(self):
        """
        Finds the corner of the distillation region
        :return: coordinate tuple; (-1, -1) if not found
        """
        for qi in range(self.dimension_i):
            for qj in range(self.dimension_j):
                if self.placement_map[qi][qj] == MapCellType.DISTILLATION:
                    return qi, qj

        return -1, -1

    def get_potential_data_patches_coordinates_2d(self):
        """
        Returns a set of 2D coordinates where data qubits can be stored
        :return: set of coordinate tuples
        """
        ret = []

        for qi in range(self.dimension_i):
            for qj in range(self.dimension_j):
                if self.placement_map[qi][qj] == MapCellType.QUBIT:
                    ret.append((qi, qj))

        return ret

    def get_potential_ancilla_patches_coordinates_2d(self):
        """
        Returns a set of 2D coordinates where ancilla patches can be stored
        :return: set of coordinate tuples
        """
        ret = []

        for qi in range(self.dimension_i):
            for qj in range(self.dimension_j):
                if self.placement_map[qi][qj] == MapCellType.ANCILLA:
                    ret.append((qi, qj))

        #
        # Assuming this is not used in the wrong way
        # There is space for an ancilla after a distillation was performed
        # Without rotating the patch
        # Next to the hardcoded A state coordinates, are the X touch patch coordinates
        #
        coord_a_state = self.circuit_qubits_to_patches["A"]
        coord_x_touch_a_state = (coord_a_state[0], coord_a_state[1] + 1)
        ret.append(coord_x_touch_a_state)

        return ret

    def read_map(self):
        print("read_map not implemented\n")

    def save_map(self):
        print("read_map not implemented\n")

