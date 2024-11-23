import logging
from models.map import Map
from response.map_info_response import MapInfoResponse

class GameStateResponse:
    ID = 'id'
    TIMESTAMP = 'timestamp'
    MAP_INFO = 'map_info'
    TAG = 'tag'
    PLAYER_ID = 'player_id'
    GAME_REMAIN_TIME = 'gameRemainTime'
    def __init__(self, *args):
        (
            id, timestamp, map_info, 
            tag, player_id, game_remain_time,
        ) = args
        self.id = id
        self.timestamp = timestamp
        self.map_info = MapInfoResponse(
            map_info.get(MapInfoResponse.SIZE),
            map_info.get(MapInfoResponse.PLAYERS),
            map_info.get(MapInfoResponse.MAP),
            map_info.get(MapInfoResponse.BOMBS),
            map_info.get(MapInfoResponse.SPOILS),
            map_info.get(MapInfoResponse.WEAPON_HAMMERS),
            map_info.get(MapInfoResponse.WEAPON_WINDS),
            map_info.get(MapInfoResponse.CELL_SIZE),
            map_info.get(MapInfoResponse.GAME_STATUS),
        )
        self.tag = tag
        self.player_id = player_id
        self.game_remain_time = game_remain_time

    def is_in_bound(self, location):
        return 0 < location[0] < self.map_info.size.rows - 1 and 0 < location[1] < self.map_info.size.cols - 1
    
    def is_occupied(self, location, enemy_location):
        bomb_locations = [bomb.location for bomb in self.map_info.bombs]
        if not self.is_in_bound(location):
            return True
        is_occupied_by_block = (self.map_info.map.matrix[location[0]][location[1]] == Map.BRICK_WALL 
                or self.map_info.map.matrix[location[0]][location[1]] == Map.BALK 
                or self.map_info.map.matrix[location[0]][location[1]] == Map.WALL 
                or self.map_info.map.matrix[location[0]][location[1]] == Map.PRISON 
                or location == enemy_location)
        if bomb_locations:
            return is_occupied_by_block or location in bomb_locations
        return is_occupied_by_block
    
    def is_brick_wall(self, location):
        if not self.is_in_bound(location):
            return False
        return self.map_info.map.matrix[location[0]][location[1]] == Map.BRICK_WALL
    
    def is_balk(self, location):
        if not self.is_in_bound(location):
            return False
        return self.map_info.map.matrix[location[0]][location[1]] == Map.BALK
    
    def empty_tiles(self, enemy_location):
        empty_tiles = []
        for row in range(self.map_info.size.rows):
            for col in range(self.map_info.size.cols):
                location = (row, col)
                if not self.is_occupied(location, enemy_location):
                    empty_tiles.append(location)
        return empty_tiles
    
    def brick_wall_tiles(self):
        brick_wall_tiles = []
        for row in range(self.map_info.size.rows):
            for col in range(self.map_info.size.cols):
                location = (row, col)
                if self.map_info.map.matrix[location[0]][location[1]] == Map.BRICK_WALL:
                    brick_wall_tiles.append(location)
        return brick_wall_tiles
    
    def balk_tiles(self):
        balk_tiles = []
        for row in range(self.map_info.size.rows):
            for col in range(self.map_info.size.cols):
                location = (row, col)
                if self.map_info.map.matrix[location[0]][location[1]] == Map.BALK:
                    balk_tiles.append(location)
        return balk_tiles
    
    def god_badge_tiles(self):
        god_badge_tiles = []
        for row in range(self.map_info.size.rows):
            for col in range(self.map_info.size.cols):
                location = (row, col)
                if self.map_info.map.matrix[location[0]][location[1]] == Map.GOD_BADGE:
                    god_badge_tiles.append(location)
        return god_badge_tiles
    
    def get_surrounding_tiles(self, location):
        tile_north = (location[0] - 1, location[1])
        tile_south = (location[0] + 1, location[1])
        tile_east = (location[0], location[1] + 1)
        tile_west = (location[0], location[1] - 1)

        surrounding_tiles = [tile_north, tile_south, tile_east, tile_west]

        for tile in surrounding_tiles:
            if not self.is_in_bound(tile):
                surrounding_tiles.remove(tile)
        
        return surrounding_tiles

    