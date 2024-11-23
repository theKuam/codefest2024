class BombResponse:
    ROW = 'row'
    COL = 'col'
    REMAIN_TIME = 'remainTime'
    PLAYER_ID = 'playerId'
    POWER = 'power'
    CREATED_AT = 'createdAt'
    def __init__(self, *args):
        (
            row,
            col,
            self.remainTime,
            self.playerId,
            self.power,
            self.createdAt,
        ) = args
        self.location = (row, col)