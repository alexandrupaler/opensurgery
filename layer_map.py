from enum import Enum
import math
import networkx as nx

class MapCellType(Enum):
    QUBIT = 3
    ANCILLA = 5
    DISTILLATION = 7

class LayerMap:
    def __init__(self):
        self.placement_map = []

        # initial dimensions are -1 and -1
        self.dimension_i = -1
        self.dimension_j = -1

        # hard coded dimensions of the distillation
        self.distillation_i_length = 4
        self.distillation_j_length = 8
        self.distillation_t_length = 10

        self.circuit_qubits_to_patches = {'A': (3, 0), 'ANCILLA': (4, 0)}

        self.routes = {}

    def search_patch_path(self, current_patch_coord, search_patch_coord, visited, path):
        if current_patch_coord == search_patch_coord:
            path.append(current_patch_coord)
            return current_patch_coord
        elif self.placement_map[current_patch_coord[0]][current_patch_coord[1]] != MapCellType.ANCILLA:
            # if not ancilla, it is a wall
            return None
        elif current_patch_coord in visited:
            # was already visited
            return None

        # mark as visited
        visited.append(current_patch_coord)

        # explore neighbors clockwise starting by the one on the right
        ancillas = self.get_closest_ancillas(*current_patch_coord)
        for ancilla in ancillas:
            if self.search_patch_path(ancilla, search_patch_coord, visited, path) is not None:
                path.append(current_patch_coord)
                return current_patch_coord

        return None

    def compute_routes_between_qubits(self):

        # begin version two with networkx
        grid_graph = nx.grid_2d_graph(self.dimension_i, self.dimension_j)
        for qi in range(self.dimension_i):
            for qj in range(self.dimension_j):
                if self.placement_map[qi][qj] != MapCellType.ANCILLA:
                    grid_graph.remove_node((qi, qj))
        # end new version


        for qubit1 in self.circuit_qubits_to_patches:
            for qubit2 in self.circuit_qubits_to_patches:
                if qubit1 == qubit2:
                    continue

                if self.get_route_between_qubits(qubit1, qubit2) is None:
                    # if the current paths were not computed
                    # get the coordinate of the patches
                    coord_patch1 = self.circuit_qubits_to_patches[qubit1]
                    coord_patch2 = self.circuit_qubits_to_patches[qubit2]

                    # get the closest ancillas next to the patches
                    anc_1 = self.get_closest_ancillas(*coord_patch1)[0]
                    if qubit1 == 'ANCILLA':
                        # if this ancilla, then do not search for ancilla
                        anc_1 = coord_patch1

                    anc_2 = self.get_closest_ancillas(*coord_patch2)[0]
                    if qubit2 == 'ANCILLA':
                        # if this ancilla, then do not search for ancilla
                        anc_2 = coord_patch2

                    # list of visited nodes
                    list_of_visited = []
                    # the path as a succession of ancilla cells
                    back_path = []
                    # self.search_patch_path(current_patch_coord=anc_1,
                    #                        search_patch_coord=anc_2,
                    #                        visited=list_of_visited,
                    #                        path=back_path)

                    # version two with networkx
                    back_path = nx.astar_path(grid_graph, anc_1, anc_2)
                    if qubit1 == 'ANCILLA':
                        back_path.remove(coord_patch1)
                    if qubit2 == 'ANCILLA':
                        back_path.remove(coord_patch2)

                    # end version two

                    # print(coord_patch1, coord_patch2, "path", back_path)
                    # store the paths, if something was found
                    if len(back_path) > 0:
                        self.routes[(qubit1, qubit2)] = back_path

    def get_route_between_qubits(self, qubit1, qubit2):
        patch_tuple_A = (qubit1, qubit2)
        if patch_tuple_A in self.routes:
            return self.routes[patch_tuple_A]

        patch_tuple_B = (qubit2, qubit1)
        if patch_tuple_B in self.routes:
            return list(reversed(self.routes[patch_tuple_B]))

        # there is no path computed between the two patches
        return None

    def map_circuit_qubits_to_patches(self, list_of_qubits):
        all_data_qubits = self.get_data_qubits()
        current_data_qubit_index = 0

        for qubit in list_of_qubits:
            print(all_data_qubits[current_data_qubit_index])
            self.circuit_qubits_to_patches[qubit] = all_data_qubits[current_data_qubit_index]
            current_data_qubit_index += 1

    def setup_arrangement_one(self, nr_logical_qubits):
        # we need a square
        dist_area = (self.distillation_i_length + 2) * self.distillation_j_length

        # data patches
        data_patches = nr_logical_qubits

        # total patches
        total_patches = dist_area + 1.5 * (data_patches + 2)# +2 because vertical channel

        # take the square root of the total number of patches
        dimension_sqrt = math.ceil(math.sqrt(total_patches))

        # the arrangement is considered a square
        self.dimension_i = int(dimension_sqrt)
        self.dimension_j = int(dimension_sqrt)

        # for the beginning everything is ancilla
        for i in range(self.dimension_i):
            self.placement_map.append([])
            for j in range(self.dimension_j):
                self.placement_map[i].append(MapCellType.ANCILLA)

        dim_i = self.dimension_i
        dim_j = self.dimension_j

        for i in range(dim_i):
            map_type = MapCellType.QUBIT
            if i % 3 in [1]:
                map_type = MapCellType.ANCILLA
            for j in range(dim_j):
                self.placement_map[i][j] = map_type

        for i in range(dim_i):
            self.placement_map[i][dim_j // 2] = MapCellType.ANCILLA
            self.placement_map[i][dim_j // 2 - 1] = MapCellType.ANCILLA

        # four cells on the first row are distillation
        # assume dimensions are sufficiently large
        for i in range(self.distillation_i_length):
            for j in range(self.distillation_j_length):
                self.placement_map[i][j] = MapCellType.DISTILLATION

        # map the logical qubits to data patches
        self.map_circuit_qubits_to_patches(list(range(nr_logical_qubits)))

        # compute the distances between the patches
        self.compute_routes_between_qubits()


    def get_closest_ancillas(self, qub_i, qub_j):
        '''
        Gets the closest ancilla next to a data qubit specified as i,j coordinates
        :param qubit: start qubit 2D coordinates
        :return: tuple of 2D coordinates, or (-1, -1) if something went wrong
        '''
        # ancilla = (-1, -1)
        ancillas = []

        # search in the immediate neighbourhood
        for qt in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            n_q1 = qub_i + qt[0]
            n_q2 = qub_j + qt[1]

            # negative indices are dangerous in python
            if n_q1 < 0 or n_q2 < 0 or n_q1 >= self.dimension_i or n_q2 >= self.dimension_j:
                continue

            n_cell_type = self.placement_map[n_q1][n_q2]

            if n_cell_type == MapCellType.ANCILLA:
                # ancilla = (n_q1, n_q2)
                ancillas.append((n_q1, n_q2))

        return ancillas

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

    def get_data_qubits(self):
        """
        Returns a set of coordinates where data qubits can be stored
        :return: set of coordinate tuples
        """
        ret = []

        for qi in range(self.dimension_i):
            for qj in range(self.dimension_j):
                if self.placement_map[qi][qj] == MapCellType.QUBIT:
                    ret.append((qi, qj))

        return ret

    def read_map(self):
        print("read_map not implemented\n")

    def save_map(self):
        print("read_map not implemented\n")

