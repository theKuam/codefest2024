from collections import defaultdict
import time

from response.bomb_response import BombResponse
from response.game_state_response import GameStateResponse

EXTENDED_DANGER_PERIOD = 1

class BombTracker:
    def __init__(self):
        self.active_bombs = {}
        self.extended_danger_zones = defaultdict(float)

    def update_bombs(self, bombs_from_server, game_state: GameStateResponse):
        current_time = time.time()
        new_active_bombs = {}

        for bomb in bombs_from_server:
            explosion_time = current_time + bomb.remainTime / 1000
            new_active_bombs[bomb.location] = explosion_time
            self.update_extended_danger_zone(bomb, game_state)

        # Track bombs that disappeared but may still affect tiles
        for location, explosion_time in self.active_bombs.items():
            if location not in new_active_bombs:
                # Bomb has "disappeared"; apply extended safety period
                affected_tiles = self.get_bomb_impact_area(BombResponse(location[0], location[1], 0, 0, 2, 0), game_state)
                for tile in affected_tiles:
                    self.extended_danger_zones[tile] = current_time + EXTENDED_DANGER_PERIOD

        # Update active bombs
        self.active_bombs = new_active_bombs

        # Clean up extended danger zones that are safe
        self.extended_danger_zones = {tile: end_time for tile, end_time in self.extended_danger_zones.items()
                                      if end_time > current_time}

    def update_extended_danger_zone(self, bomb, game_state: GameStateResponse):
        current_time = time.time()
        affected_tiles = self.get_bomb_impact_area(bomb, game_state)
        for tile in affected_tiles:
            self.extended_danger_zones[tile] = current_time + EXTENDED_DANGER_PERIOD

    def is_tile_safe(self, tile):
        current_time = time.time()
        return tile not in self.extended_danger_zones or self.extended_danger_zones[tile] <= current_time
    
    def get_bomb_impact_area(self, bomb: BombResponse, game_state: GameStateResponse):
        affected_tiles = set()

        for i in range(1, bomb.power + 2):
            if game_state.is_in_bound((bomb.location[0] + i, bomb.location[1])):
                affected_tiles.add((bomb.location[0] + i, bomb.location[1]))  # Down
            if game_state.is_in_bound((bomb.location[0] - i, bomb.location[1])):
                affected_tiles.add((bomb.location[0] - i, bomb.location[1]))  # Up
            if game_state.is_in_bound((bomb.location[0], bomb.location[1] + i)):
                affected_tiles.add((bomb.location[0], bomb.location[1] + i)) # Right
            if game_state.is_in_bound((bomb.location[0], bomb.location[1] - i)):
                affected_tiles.add((bomb.location[0], bomb.location[1] - i)) # Left
                
        affected_tiles.add((bomb.location[0], bomb.location[1]))  # Add bomb's own tile
        return affected_tiles