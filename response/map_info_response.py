from models.map import Map
from models.size import Size
from response.bomb_response import BombResponse
from response.player_resonse import PlayerResponse
from response.spoil_response import SpoilResponse


class MapInfoResponse:
    SIZE = 'size'
    PLAYERS = 'players'
    MAP = 'map'
    BOMBS = 'bombs'
    SPOILS = 'spoils'
    WEAPON_HAMMERS = 'weaponHammers'
    WEAPON_WINDS = 'weaponWinds'
    CELL_SIZE = 'cellSize'
    GAME_STATUS = 'gameStatus'

    def __init__(self, *args):
        (
            size, players, _map, bombs, spoils, weaponHammers, 
            weaponWinds, cellSize, gameStatus,
        ) = args
        
        self.size = Size(
            size.get(Size.ROWS),
            size.get(Size.COLS),
        )
        self.players = list(
            map(
                lambda player: PlayerResponse(
                    player.get(PlayerResponse.ID),
                    player.get(PlayerResponse.SPAWN_BEGIN),
                    player.get(PlayerResponse.CURRENT_POSITION),
                    player.get(PlayerResponse.POWER),
                    player.get(PlayerResponse.SPEED),
                    player.get(PlayerResponse.DELAY),
                    player.get(PlayerResponse.SCORE),
                    player.get(PlayerResponse.LIVES),
                    player.get(PlayerResponse.BOX),
                    player.get(PlayerResponse.STICKY_RICE),
                    player.get(PlayerResponse.CHUNG_CAKE),
                    player.get(PlayerResponse.NINE_TUSK_ELEPHANT),
                    player.get(PlayerResponse.NINE_SPUR_ROOSTER),
                    player.get(PlayerResponse.NINE_MANE_HAIR_HORSE),
                    player.get(PlayerResponse.HOLY_SPIRIT_STONE),
                    player.get(PlayerResponse.ETERNAL_BADGE),
                    player.get(PlayerResponse.BRICK_WALL),
                    player.get(PlayerResponse.TRANSFORM_TYPE),
                    player.get(PlayerResponse.HAS_TRANSFORM),
                    player.get(PlayerResponse.OWNER_WEAPON),
                    player.get(PlayerResponse.CUR_WEAPON),
                    player.get(PlayerResponse.IS_STUN),
                    player.get(PlayerResponse.TIME_TO_USE_SPECIAL_WEAPONS),
                ),
                players,
            )
        )
        self.map = Map(
            size.get(Size.ROWS),
            size.get(Size.COLS),
            _map,
        )
        self.bombs = list(
            map(
                lambda bomb: BombResponse(
                    bomb.get(BombResponse.ROW),
                    bomb.get(BombResponse.COL),
                    bomb.get(BombResponse.REMAIN_TIME),
                    bomb.get(BombResponse.PLAYER_ID),
                    bomb.get(BombResponse.POWER),
                    bomb.get(BombResponse.CREATED_AT),
                ),
                bombs,
            )
        )
        self.spoils = list(
            map(
                lambda spoil: SpoilResponse(
                    spoil.get(SpoilResponse.ROW),
                    spoil.get(SpoilResponse.COL),
                    spoil.get(SpoilResponse.SPOIL_TYPE),
                ),
                spoils,
            )
        )
        self.weaponHammers = weaponHammers
        self.weaponWinds = weaponWinds
        self.cellSize = cellSize
        self.gameStatus = gameStatus
