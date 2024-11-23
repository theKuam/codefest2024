class PlayerActionRequest:
    ACTION = 'action'
    PAYLOAD = 'payload'
    DESTINATION = 'destination'
    ROW = 'row'
    COL = 'col'
    CHARACTER_TYPE = 'characterType'
    def __init__(self, action: str, row: int = None, col: int = None, characterType: str = None):
        
        self.action = action
        if row != None and col != None:
            self.destination = (row, col)
        else:
            self.destination = None
        self.characterType = characterType

    def getPlayerActionRequest(self):
        if self.characterType != None and self.destination != None:
            return {
                PlayerActionRequest.ACTION: self.action,
                PlayerActionRequest.PAYLOAD: {
                    PlayerActionRequest.DESTINATION: {
                        PlayerActionRequest.ROW: self.destination[0],
                        PlayerActionRequest.COL: self.destination[1],
                    },
                    PlayerActionRequest.CHARACTER_TYPE: self.characterType,
                },
            }
        elif self.characterType != None and self.destination == None:
            return {
                PlayerActionRequest.ACTION: self.action,
                PlayerActionRequest.PAYLOAD: {
                    PlayerActionRequest.CHARACTER_TYPE: self.characterType,
                },
            }
        elif self.characterType == None and self.destination != None:
            return {
                PlayerActionRequest.ACTION: self.action,
                PlayerActionRequest.PAYLOAD: {
                    PlayerActionRequest.DESTINATION: {
                        PlayerActionRequest.ROW: self.destination[0],
                        PlayerActionRequest.COL: self.destination[1],
                    },
                },
            }
        else:
            return {
                PlayerActionRequest.ACTION: self.action,
            }