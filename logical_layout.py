from enum import Enum


class MapCellType(Enum):
    QUBIT = 3
    ANCILLA = 5
    DISTILLATION = 7

class LogicalLayout:
    def __init__(self, si, sj):
        self.placement_map = []

        self.dimension_i = si
        self.dimension_j = sj

        for i in range(self.dimension_i):
            self.placement_map.append([])
            for j in range(self.dimension_j):
                self.placement_map[i].append(MapCellType.ANCILLA)

        self.setup_arrangement_one()

    def setup_arrangement_one(self):
        dim_i = self.dimension_i
        dim_j = self.dimension_j

        for i in range(dim_i):
            map_type = MapCellType.QUBIT
            if i % 2 == 1:
                map_type = MapCellType.ANCILLA
            for j in range(dim_j):
                self.placement_map[i][j] = map_type

        # four cells on the first row are distillation
        # assume dimensions are sufficiently large
        for i in range(3):
            for j in range(4):
                self.placement_map[i][j] = MapCellType.DISTILLATION

    def read_map(self):
        print("read_map not implemented\n")

    def save_map(self):
        print("read_map not implemented\n")

