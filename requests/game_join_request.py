class GameJoiningRequest:
    GAME_ID = 'game_id'
    PLAYER_ID = 'player_id'

    def __init__(self, game_id: str, player_id: str):
        self.game_id = game_id
        self.player_id = player_id

    def getGameJoiningRequest(self):
        return {
            self.GAME_ID: self.game_id,
            self.PLAYER_ID: self.player_id,
        }