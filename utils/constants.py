from enum import Enum

class SocketEvent(Enum):
    JOIN_GAME = 'join game'
    TICKTACK_PLAYER = 'ticktack player'
    DRIVE_PLAYER = 'drive player'
    REGISTER_CHARACTER_POWER = 'register character power'
    ACTION = 'action'

class GameTagHeader(Enum):
    PLAYER = 'player:'
    BOMB = 'bomb:'
    HAMMER = 'hammer:'
    WOODEN_PESTLE = 'wooden-pestle:'
    WIND = 'wind:'

class GameTag(Enum):
    # Player tag
    PLAYER_MOVING_BANNED = GameTagHeader.PLAYER.value + 'moving-banned'
    PLAYER_START_MOVING = GameTagHeader.PLAYER.value + 'start-moving'
    PLAYER_STOP_MOVING = GameTagHeader.PLAYER.value + 'stop-moving'
    PLAYER_BE_ISOLATED = GameTagHeader.PLAYER.value + 'be-isolated'
    PLAYER_BACK_TO_PLAYGROUND = GameTagHeader.PLAYER.value + 'back-to-playground'
    PLAYER_PICK_SPOIL = GameTagHeader.PLAYER.value + 'pick-spoil'
    PLAYER_STUN_BY_WEAPON = GameTagHeader.PLAYER.value + 'stun-by-weapon'
    PLAYER_STUN_TIMEOUT = GameTagHeader.PLAYER.value + 'stun-timeout'
    PLAYER_INTO_WEDDING_ROOM = GameTagHeader.PLAYER.value + 'into-wedding-room'
    PLAYER_OUTTO_WEDDING_ROOM = GameTagHeader.PLAYER.value + 'outto-wedding-room'
    PLAYER_COMPLETED_WEDDING = GameTagHeader.PLAYER.value + 'completed-wedding'

    # Bomb tag
    BOMB_EXPLODED = GameTagHeader.BOMB.value + 'exploded'
    BOMB_SETUP = GameTagHeader.BOMB.value + 'setup'

    # Game tag
    START_GAME = 'start-game'
    UPDATE_DATA = 'update-data'

    # Weapon tag
    HAMMER_EXPLODED = GameTagHeader.HAMMER.value + 'exploded'
    WOODEN_PESTLE_SETUP = GameTagHeader.WOODEN_PESTLE.value + 'setup'
    WIND_EXPLODED = GameTagHeader.WIND.value + 'exploded'

class SpoilType(Enum):
    # SPOIL_TYPE = (value, score)
    STICKY_RICE = (32, 1)
    CHUNG_CAKE = (33, 2)
    NINE_TUSK_ELEPHANT = (34, 5)
    NINE_SPURS_ROOSTER = (35, 3)
    NINE_MANE_HAIR_HORSE = (36, 4)
    HOLY_SPIRIT_STONE = (37, 3)

class Drive(Enum):
    LEFT = '1'
    RIGHT = '2'
    UP = '3'
    DOWN = '4'
    BOMB = 'b'
    STOP = 'x'

class Action(Enum):
    SWITCH_WEAPON = 'switch weapon'
    USE_WEAPON = 'use weapon'
    MARRY_WIFE = 'marry wife'

class Phase(Enum):
    BOMB_PHASE = 'bomb phase'
    PHASE_1 = 'finding god badges'
    PHASE_2 = 'finding treasures'
    PHASE_3 = 'god clash'

class Weapon(Enum):
    WOODEN_PESTLE = 1
    BOMB = 2

SECOND = 1000