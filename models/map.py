import numpy as np

class Map:
    EMPTY = 0
    WALL = 1
    BALK = 2
    BRICK_WALL = 3
    PRISON = 5
    GOD_BADGE = 6
    SPECIAL_WALL = 7

    ROW = 'row'
    COL = 'col'

    def __init__(self, *args):
        (
            rows,
            cols,
            matrix,
        ) = args
        self.rows = rows
        self.cols = cols
        self.matrix = np.zeros((rows, cols))
        for i in range(rows):
            for j in range(cols):
                self.matrix[i][j] = matrix[i][j]
