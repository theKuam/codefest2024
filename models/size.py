class Size:
    ROWS = "rows"
    COLS = "cols"
    def __init__(self, *args):
        (
            self.rows,
            self.cols,
        ) = args