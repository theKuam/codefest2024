from models.map import Map


class PlayerResponse:
    ID = 'id'
    SPAWN_BEGIN = 'spawnBegin'
    CURRENT_POSITION = 'currentPosition'
    POWER = 'power'
    SPEED = 'speed'
    DELAY = 'delay'
    SCORE = 'score'
    LIVES = 'lives'
    BOX = 'box'
    STICKY_RICE = 'stickyRice'
    CHUNG_CAKE = 'chungCake'
    NINE_TUSK_ELEPHANT = 'nineTuskElephant'
    NINE_SPUR_ROOSTER = 'nineSpurRooster'
    NINE_MANE_HAIR_HORSE = 'nineManeHairHorse'
    HOLY_SPIRIT_STONE = 'holySpiritStone'
    ETERNAL_BADGE = 'eternalBadge'
    BRICK_WALL = 'brickWall'
    TRANSFORM_TYPE = 'transformType'
    HAS_TRANSFORM = 'hasTransform'
    OWNER_WEAPON = 'ownerWeapon'
    CUR_WEAPON = 'currentWeapon'
    IS_STUN = 'isStun'
    TIME_TO_USE_SPECIAL_WEAPONS = 'timeToUseSpecialWeapons'

    cell_pixels = 35
    second_per_move = 10
    player_speed_rate = 1 / 60

    def __init__(self, *args):
        (
            self.id,
            self.spawnBegin,
            currentPosition,
            self.power,
            self.speed,
            self.delay,
            self.score,
            self.lives,
            self.box,
            self.stickyRice,
            self.chungCake,
            self.nineTuskElephant,
            self.nineSpursRooster,
            self.nineManeHairHorse,
            self.holySpiritStone,
            self.eternalBadge,
            self.brickWall,
            self.transformType,
            self.hasTransform,
            self.ownerWeapon,
            self.curWeapon,
            self.isStun,
            self.timeToUseSpecialWeapons
        ) = args
        self.currentPosition = (
            currentPosition.get(Map.ROW),
            currentPosition.get(Map.COL),
        )

    def real_speed(self):
        return (self.cell_pixels / (self.player_speed_rate * self.speed)) * self.second_per_move