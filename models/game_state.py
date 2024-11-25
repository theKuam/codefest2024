from .map_info import MapInfo

class GameStateResponse:
    def __init__(self, response):
        self.id = response.get('id')
        self.timestamp = response.get('timestamp')
        self.map_info = MapInfo(response.get('map_info', {}))
        self.tag = response.get('tag')
        self.player_id = response.get('player_id')
        self.game_remain_time = response.get('gameRemainTime')