class PlayerDriveRequest:
    DIRECTION = 'direction'

    def __init__(self, direction: str):
        self.direction = direction

    def getPlayerDriveRequest(self):
        return {
            self.DIRECTION: self.direction,
        }