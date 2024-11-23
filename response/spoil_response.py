from utils import constants


class SpoilResponse:
    ROW = 'row'
    COL = 'col'
    SPOIL_TYPE = 'spoil_type'
    def __init__(self, *args):
        (
            row,
            col,
            self.spoil_type,
        ) = args
        self.location = (row, col)

    def isValid(self):
        return any(item.value[0] == self.spoil_type for item in constants.SpoilType)
        