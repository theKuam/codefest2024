from .player import PlayerResponse
from .bomb import Bomb
from .spoil import Spoil
from .weapon_hammer import WeaponHammer
from .weapon_wind import WeaponWind
from .map_matrix import MapMatrix

class MapInfo:
    def __init__(self, response):
        self.size = response.get('size')
        self.players = [PlayerResponse(p) for p in response.get('players', [])]
        self.map_matrix = MapMatrix(response.get('map', []))
        self.bombs = [Bomb(b) for b in response.get('bombs', [])]
        self.spoils = [Spoil(s) for s in response.get('spoils', [])]
        self.weapon_hammers = [WeaponHammer(w) for w in response.get('weaponHammers', [])]
        self.weapon_winds = [WeaponWind(w) for w in response.get('weaponWinds', [])]
        self.cell_size = response.get('cellSize')
        self.game_status = response.get('gameStatus')
        self.tag = response.get('tag')
        self.player_id = response.get('playerId')
        self.game_remain_time = response.get('gameRemainTime')

class Size:
    def __init__(self, response):
        self.rows = response.get('rows')
        self.cols = response.get('cols')

