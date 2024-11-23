from collections import Counter, defaultdict, deque
import logging
import random
from models.bomb_tracker import BombTracker
from response.bomb_response import BombResponse
from response.game_state_response import GameStateResponse
from response.player_resonse import PlayerResponse
from strategy.a_star import a_star, a_star_include_brick_wall
from strategy.distance import manhattan_distance
from utils import constants

bomb_tracker = BombTracker()
is_transforming = False

current_phase = constants.Phase.PHASE_1
bomb_phase = constants.Phase.BOMB_PHASE
my_spoil_type = []

def get_my_player_state(game_state: GameStateResponse, player_id: str):
    for player in game_state.map_info.players:
        if player.id == player_id:
            return player
    return None

def get_enemy_state(game_state: GameStateResponse, player_id: str):
    for player in game_state.map_info.players:
        if player.id != player_id:
            return player
    return None

# Phase 1: Collect God Badge
def is_phase_1(my_player_state: PlayerResponse):
    return not my_player_state.hasTransform

def next_move(game_state: GameStateResponse, my_player_state: PlayerResponse, current_my_bomb_location = None):
    global current_phase
    global bomb_phase
    global is_transforming

    location = my_player_state.currentPosition
    enemy_state = get_enemy_state(game_state, my_player_state.id)
    enemy_location = enemy_state.currentPosition
    bombs = game_state.map_info.bombs
    
    if my_player_state.hasTransform:
        is_transforming = False
    elif is_transforming:
        return ([], constants.Drive.STOP.value, location, False), bomb_phase, current_phase

    if bombs or (current_my_bomb_location):
        bomb_phase = constants.Phase.BOMB_PHASE
        if current_my_bomb_location and not any(bomb.location == current_my_bomb_location for bomb in bombs):
                bombs.append(BombResponse(current_my_bomb_location[0], current_my_bomb_location[1], my_player_state.delay, my_player_state.id, my_player_state.power, 0))
        return next_move_avoid_bombs(location, game_state, my_player_state, enemy_location, bombs), bomb_phase, current_phase
    else:
        bomb_phase = None
    if is_phase_1(my_player_state):
        current_phase = constants.Phase.PHASE_1
        return next_move_phase_1(location, game_state, enemy_location), bomb_phase, current_phase
    else:
        current_phase = constants.Phase.PHASE_2
        return next_move_phase_2(location, game_state, enemy_location), bomb_phase, current_phase
    
def next_move_avoid_bombs(location, game_state: GameStateResponse, my_player_state: PlayerResponse, enemy_location, bombs):
    safest_tiles, impact_list = find_safest_tiles(bombs, game_state, my_player_state, enemy_location)
    target, path = find_best_reachable_tile(location, safest_tiles, game_state, enemy_location, None, impact_list)
    if target:
        return path, get_moves(path), target, game_state.is_brick_wall(target)
    return [], constants.Drive.STOP.value, target, False

def next_move_phase_1(location, game_state: GameStateResponse, enemy_location):
    global is_transforming

    if location in game_state.god_badge_tiles():
        is_transforming = True
        return [], constants.Drive.STOP.value, location, False
    god_badges = game_state.god_badge_tiles()
    nearest_god_badge = (float('inf'), None, None)
    for god_badge in god_badges:
        pseudo_god_badge_path = a_star_include_brick_wall(location, god_badge, game_state, enemy_location)
        if god_badge == enemy_location or not pseudo_god_badge_path:
            continue
        distance = manhattan_distance(location, god_badge)
        if distance < nearest_god_badge[0]:
            nearest_god_badge = (distance, god_badge, pseudo_god_badge_path)
    god_badge_path = a_star(location, nearest_god_badge[1], game_state, enemy_location)
    if god_badge_path:
        return god_badge_path, get_moves(god_badge_path), nearest_god_badge[1], False
    brick_wall_on_path = [tile for tile in nearest_god_badge[2] if game_state.is_brick_wall(tile)]
    target, path = find_best_reachable_tile(location, brick_wall_on_path, game_state, enemy_location, nearest_god_badge[1])
    if target:
        return path, get_moves(path), target, game_state.is_brick_wall(target)
    return [], constants.Drive.STOP.value, target, False

def next_move_phase_2(location, game_state: GameStateResponse, enemy_location):
    target, path = find_best_reachable_tile(location, game_state.balk_tiles(), game_state, enemy_location, empty_tiles = game_state.empty_tiles(enemy_location))
    if target:
        return path, get_moves(path), target, game_state.is_balk(target) or any(game_state.is_balk(tile) for tile in game_state.get_surrounding_tiles(target))
    return [], constants.Drive.STOP.value, target, False
    

def find_safest_tiles(bombs: list, game_state: GameStateResponse, my_player_state: PlayerResponse, enemy_location):
    bomb_tracker.update_bombs(bombs, game_state)
    tile_safety = defaultdict(int)

    # Calculate the impact score for each tile affected by bombs
    for bomb in bombs:
        affected_tiles = bomb_tracker.get_bomb_impact_area(bomb, game_state)
        for tile in affected_tiles:
            if manhattan_distance(tile, my_player_state.currentPosition) == 0:
                tile_safety[tile] += max(0.5, float((2 * constants.SECOND - bomb.remainTime) / constants.SECOND)) + 10
            else:
                tile_safety[tile] += max(0.5, float((2 * constants.SECOND - bomb.remainTime) / constants.SECOND) + 1/manhattan_distance(tile, my_player_state.currentPosition))
    
    # Find safe tiles and their impact scores
    safest_tiles = []
    impact_list = defaultdict(int)
    
    for empty_tile in game_state.empty_tiles(enemy_location):
        safest_tiles.append(empty_tile)
        impact_list[empty_tile] = tile_safety.get(empty_tile, 0)
        
    return safest_tiles, impact_list

def move_to_tile(current_location, target_location):
    current_tuple = (current_location[0], current_location[1])
    target_tuple = (target_location[0], target_location[1])
    diff = tuple(x-y for x, y in zip(target_tuple, current_tuple))

    if diff == (0, 1):
        drive = constants.Drive.RIGHT.value
    elif diff == (0, -1):
        drive = constants.Drive.LEFT.value
    elif diff == (1, 0):
        drive = constants.Drive.DOWN.value
    elif diff == (-1, 0):
        drive = constants.Drive.UP.value
    else:
        drive = constants.Drive.STOP.value
    
    return drive

def get_reachable_tiles(location, tiles: list, game_state: GameStateResponse, enemy_location, bomb_impact_list = None):
    reachable_tiles = []
    for tile in tiles:
        path_to_tile = a_star(location, tile, game_state, enemy_location, tiles, bomb_impact_list)
        if path_to_tile:
            reachable_tiles.append((tile, path_to_tile))
        if bomb_impact_list:
            continue
        for surrounding_tile in game_state.get_surrounding_tiles(tile):
                if game_state.is_occupied(surrounding_tile, enemy_location):
                    continue
                else:
                    path_to_surround_tile = a_star(location, surrounding_tile, game_state, enemy_location, tiles, bomb_impact_list)
                    if path_to_surround_tile:
                        reachable_tiles.append((surrounding_tile, path_to_surround_tile))
    return reachable_tiles

def find_best_reachable_tile(location, tiles: list, game_state: GameStateResponse, enemy_location, nearest_god_badge = None, bomb_impact_list = None, empty_tiles = None):
    global my_spoil
    if empty_tiles:
        reachable_tiles = get_reachable_tiles(location, tiles + empty_tiles, game_state, enemy_location, bomb_impact_list)
        not_empty_reachable_tiles = get_reachable_tiles(location, tiles, game_state, enemy_location, bomb_impact_list)
    else:
        reachable_tiles = get_reachable_tiles(location, tiles, game_state, enemy_location, bomb_impact_list)
        not_empty_reachable_tiles = reachable_tiles
    if not reachable_tiles:
        return None, None
    
    obtainable_spoils = []
    map_spoil = game_state.map_info.spoils
    for spoil in map_spoil:
        if any(tile[0] == spoil.location for tile in reachable_tiles) and spoil.spoil_type not in my_spoil_type:
            obtainable_spoils.append((spoil, next((tile[1] for tile in reachable_tiles if tile[0] == spoil.location), None)))
    if obtainable_spoils:
        return find_best_path_to_spoil(obtainable_spoils, location, reachable_tiles, nearest_god_badge, bomb_impact_list)
    else:
        return find_best_path(location, not_empty_reachable_tiles, nearest_god_badge, bomb_impact_list)
    

def get_moves(path):
    moves = ''
    for i in range(0, len(path) - 1):
        moves += move_to_tile(path[i], path[i + 1])
    return moves

def is_safe(path, bombs, game_state, my_player_state, enemy_location):
    safe_tiles = find_safest_tiles(bombs, game_state, my_player_state, enemy_location)[0]
    # check if all tiles in path are safe
    return all(tile in safe_tiles for tile in path)

def find_best_path_to_spoil(spoils, location, tiles, nearest_god_badge = None, bomb_impact_list = None):
    global my_spoil_type
    
    if len(my_spoil_type) == 0:
        best_spoil_path = [(item[0].location, item[1]) for item in spoils]
    else:
        spoil_counts = Counter(my_spoil_type)
        best_spoil = spoil_counts.most_common(1)[0]
        best_spoil_path = [(item[0].location, item[1]) for item in spoils if item[0].spoil_type == best_spoil]
        if not best_spoil_path:
            best_spoil_path = [(item[0].location, item[1]) for item in spoils]
    

    if bomb_impact_list:
        for key, impact in bomb_impact_list.items():
            if impact > 0:
                logging.debug(f'impact {key} {impact}')
        min_impact_target = min(tiles, key=lambda item: (bomb_impact_list.get(item[0], 0)))
        logging.debug(f'min_impact_target {min_impact_target[0]} {bomb_impact_list.get(min_impact_target[0], 0)}')
        min_impact_value = bomb_impact_list.get(min_impact_target[0], 0)
        min_impact_targets = [item for item in tiles if bomb_impact_list.get(item[0], 0) == min_impact_value]
        logging.debug(f'min_impact_targets {min_impact_targets}')
        min_impact = min(min_impact_targets, key=lambda item: sum(bomb_impact_list[tile] for tile in item[1]))
        logging.debug(f'min_impact {min_impact} {sum(bomb_impact_list[tile] for tile in min_impact[1])}')
        min_impact_tiles = [item for item in tiles if bomb_impact_list[tiles.index(item)] == bomb_impact_list[tiles.index(min_impact)]]
        logging.debug(f'min_impact_tiles {min_impact_tiles}')
        min_impact_path = min(min_impact_tiles, key=lambda item: len(item[1]))
        my_spoil_type = [spoil.spoil_type for spoil, _ in spoils if spoil.location == min_impact_path[0]]
        logging.debug(f'min_impact_path {min_impact_path} best_impact {sum(bomb_impact_list[tile] for tile in min_impact_path[1])}')
        return min_impact_path
    if nearest_god_badge:
        path = min(best_spoil_path, key=lambda item: (len(item[1]),))
        my_spoil_type = [spoil.spoil_type for spoil, _ in spoils if spoil.location == path[0]]
        return path
    path = min(best_spoil_path, key=lambda item: (len(item[1]), manhattan_distance(location, item[0])))
    my_spoil_type = [spoil.spoil_type for spoil, _ in spoils if spoil.location == path[0]]
    return path 

def find_best_path(location, tiles, nearest_god_badge = None, bomb_impact_list = None):
    if bomb_impact_list:
        # Find tiles with minimum impact
        min_impact_target = min(tiles, key=lambda item: (bomb_impact_list.get(item[0], 0)))
        min_impact_value = bomb_impact_list.get(min_impact_target[0], 0)
        min_impact_targets = [item for item in tiles if bomb_impact_list.get(item[0], 0) == min_impact_value]
        
        # Among those, find the path with minimum total impact
        min_impact = min(min_impact_targets, key=lambda item: sum(bomb_impact_list.get(tile, 0) for tile in item[1]))
        
        # Find all paths with the same minimum total impact
        min_total_impact = sum(bomb_impact_list.get(tile, 0) for tile in min_impact[1])
        min_impact_tiles = [item for item in min_impact_targets 
                          if sum(bomb_impact_list.get(tile, 0) for tile in item[1]) == min_total_impact]
        
        # Among those, choose the shortest path
        min_impact_path = min(min_impact_tiles, key=lambda item: len(item[1]))
        return min_impact_path
    if nearest_god_badge:
        path = min(tiles, key=lambda item: (len(item[1]),))
        return path
    path = min(tiles, key=lambda item: (len(item[1]), manhattan_distance(location, item[0])))
    logging.debug(f'best path {path}')
    return path