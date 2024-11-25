from typing import Dict, List, Tuple, Set
import logging
from models.player import PlayerResponse
from models.game_state import GameStateResponse
from utils.constants import Tile
from utils.constants import Weapon
from models.spoil import Spoil
from utils.constants import SpoilType
from utils.constants import Drive
from utils.constants import Action
import random
from time import time

# Constants
MOVE_TIME = 100  # ms per move
SAFETY_MARGIN = 300  # additional safety margin in ms

# Add to global variables
enemy_positions_history = {}  # {player_id: [positions]}
last_attack_time = time()
ATTACK_COOLDOWN = 2.0  # Seconds between attack attempts
last_positions = []  # Track our own last positions
POSITION_HISTORY = 8  # How many of our positions to remember
last_loop_break_time = 0
LOOP_BREAK_DURATION = 2.0  # Duration of loop breaking behavior
current_strategy = 'collect'   # 'collect' or 'attack'
STRATEGY_DURATION = 5.0       # Minimum seconds before considering strategy change
consecutive_stops = 0  # Track consecutive STOP actions
last_action = None
EXPLOSION_DELAY = 500  # ms to wait after explosion
last_explosion_time = 0
match_start_time = None
COLLECTION_PHASE_START = 120  # seconds after match start

# Global variable to track if we've faced the wall
faced_wall = False
standing_on_god = False

# Add to global variables at the top
move_counter = 0
SPECIAL_WEAPON_CHECK_INTERVAL = 10  # Check every 10 moves

def get_bomb_danger_tiles(game_state, additional_bomb_pos=None):
    """Get all tiles that are in danger from bombs."""
    danger_tiles = {}
    
    # Add danger from existing bombs
    for bomb in game_state.map_info.bombs:
        # Add bomb's own position
        danger_tiles[bomb.position] = bomb.remain_time
        
        # Add tiles in bomb's range
        for direction in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            for distance in range(1, bomb.power + 1):
                row = bomb.position[0] + direction[0] * distance
                col = bomb.position[1] + direction[1] * distance
                pos = (row, col)
                
                # Stop if we hit a wall or balk
                if not (0 <= row < game_state.map_info.map_matrix.rows and 
                       0 <= col < game_state.map_info.map_matrix.cols):
                    break
                    
                cell = game_state.map_info.map_matrix[row, col]
                if cell in [Tile.WALL.value, Tile.BALK.value, Tile.BRICK_WALL.value]:
                    break
                    
                # Add to danger tiles with bomb's remain time
                if pos not in danger_tiles or bomb.remain_time < danger_tiles[pos]:
                    danger_tiles[pos] = bomb.remain_time
    
    # Add danger from hypothetical bomb if position provided
    if additional_bomb_pos:
        danger_tiles[additional_bomb_pos] = 2000  # Default bomb timer
        bomb_power = 2  # Default bomb power
        
        # Add tiles in hypothetical bomb's range
        for direction in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            for distance in range(1, bomb_power + 1):
                row = additional_bomb_pos[0] + direction[0] * distance
                col = additional_bomb_pos[1] + direction[1] * distance
                pos = (row, col)
                
                if not (0 <= row < game_state.map_info.map_matrix.rows and 
                       0 <= col < game_state.map_info.map_matrix.cols):
                    break
                    
                cell = game_state.map_info.map_matrix[row, col]
                if cell in [Tile.WALL.value, Tile.BALK.value, Tile.BRICK_WALL.value]:
                    break
                    
                if pos not in danger_tiles or 2000 < danger_tiles[pos]:
                    danger_tiles[pos] = 2000
    
    return danger_tiles

def is_walkable(game_state, position, my_id, danger_tiles=None, phase=1):
    """Check if a position is walkable and safe."""
    row, col = position
    cell = game_state.map_info.map_matrix[row, col]
    
    # Never walkable
    if cell in [Tile.WALL.value, Tile.PRISON.value, Tile.BRICK_WALL.value, Tile.BALK.value]:
        return False
        
    # Check for enemy positions
    for player in game_state.map_info.players:
        if player.id != my_id and player.current_position == position:
            return False
    
    # God badge is walkable in Phase 1
    if phase == 1 and cell == Tile.GOD_BADGE.value:
        return True
        
    # Empty spaces are always walkable
    if cell == Tile.EMPTY.value:
        return True
        
    return False

def is_reachable(game_state, position, my_id, phase=1):
    """Check if a position is reachable (can move into or can break)."""
    row, col = position
    cell = game_state.map_info.map_matrix[row, col]
    
    # Never reachable
    if cell in [Tile.WALL.value, Tile.PRISON.value]:
        return False
        
    # Phase 1: Can reach empty spaces, brick walls (to break), and god badges
    if phase == 1:
        return cell in [Tile.EMPTY.value, Tile.BRICK_WALL.value, Tile.GOD_BADGE.value]
    # Phase 2: Can reach empty spaces and balks (to bomb)
    else:
        return cell in [Tile.EMPTY.value, Tile.BALK.value]

def find_path_to_position(game_state, start_pos, target_pos, my_id, phase=1):
    """Find path to a specific position using BFS."""
    if not target_pos:
        return None
        
    queue = [(start_pos, [start_pos])]
    visited = {start_pos}
    danger_tiles = get_bomb_danger_tiles(game_state)
    
    while queue:
        current_pos, path = queue.pop(0)
        
        if current_pos == target_pos:
            return path
            
        # Try all cardinal directions
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            next_pos = (current_pos[0] + dr, current_pos[1] + dc)
            
            if next_pos not in visited:
                # Use is_reachable for target, is_walkable for path
                if next_pos == target_pos:
                    if is_reachable(game_state, next_pos, my_id, phase):
                        return path + [next_pos]
                elif (is_walkable(game_state, next_pos, my_id, danger_tiles, phase)):
                    queue.append((next_pos, path + [next_pos]))
                    visited.add(next_pos)
    
    return None

def find_escape_path(game_state, my_pos, danger_tiles, my_id, phase=1):
    """Find a safe escape path using BFS, allowing movement through danger tiles."""
    queue = [(my_pos, [my_pos], float('inf'))]  # (pos, path, min_time_seen)
    visited = {my_pos: float('inf')}  # pos: min_time_seen
    
    while queue:
        current_pos, path, min_time = queue.pop(0)
        
        # If current position is safe and has valid escape routes
        if current_pos not in danger_tiles:
            if is_safe_escape_position(game_state, current_pos, my_id, danger_tiles, phase):
                return path[1:]  # Return path excluding current position
        
        # Try all cardinal directions
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            next_pos = (current_pos[0] + dr, current_pos[1] + dc)
            
            # Check if position is within bounds and walkable
            if not (0 <= next_pos[0] < game_state.map_info.map_matrix.rows and
                   0 <= next_pos[1] < game_state.map_info.map_matrix.cols and
                   is_walkable(game_state, next_pos, my_id, None, phase)):
                continue
                
            # Calculate the minimum time we'll have when reaching this position
            next_min_time = min_time
            if next_pos in danger_tiles:
                next_min_time = min(next_min_time, danger_tiles[next_pos])
            
            # Calculate if we have enough time to reach this position
            moves_needed = len(path) + 1
            time_needed = (moves_needed * MOVE_TIME) + SAFETY_MARGIN
            
            # Skip if we don't have enough time to move through
            if next_min_time < time_needed:
                continue
            
            # Only visit if we haven't seen this position or found a safer path
            if next_pos not in visited or next_min_time > visited[next_pos]:
                visited[next_pos] = next_min_time
                queue.append((next_pos, path + [next_pos], next_min_time))
                
                # Sort queue by minimum time (prioritize safer paths)
                queue.sort(key=lambda x: x[2], reverse=True)
    
    # If we're still in danger but can't find a completely safe path,
    # try to move to the position with the longest time until explosion
    if queue:
        best_emergency_path = max(queue, key=lambda x: x[2])
        remaining_time = best_emergency_path[2] - ((len(best_emergency_path[1]) * MOVE_TIME) + SAFETY_MARGIN)
        logging.warning(f"No completely safe path found. Taking emergency path with {remaining_time}ms margin")
        return best_emergency_path[1][1:]
    
    return None

def find_spoils(game_state):
    """Find all spoils on the map with their positions and types."""
    spoils = []
    for spoil in game_state.map_info.spoils:
        spoils.append((spoil.position, spoil.spoil_type))
    return spoils

def get_spoil_priority(spoil_type, player):
    """Get priority score for a spoil type based on player's current spoils."""
    if spoil_type == SpoilType.HOLY_SPIRIT_STONE.value:
        return float('inf')  # Always highest priority
    
    # Map spoil types to player attributes
    spoil_counts = {
        SpoilType.STICKY_RICE.value: player.sticky_rice,
        SpoilType.CHUNG_CAKE.value: player.chung_cake,
        SpoilType.NINE_TUSK_ELEPHANT.value: player.nine_tusk_elephant,
        SpoilType.NINE_SPUR_ROOSTER.value: player.nine_spur_rooster,
        SpoilType.NINE_MANE_HAIR_HORSE.value: player.nine_mane_hair_horse,
    }
    
    # Return inverse of count (fewer = higher priority)
    return 1.0 / (spoil_counts.get(spoil_type, 0) + 1)

def find_nearest_holy_stone(game_state, my_pos, my_id):
    """Find the nearest reachable holy stone."""
    spoils = find_spoils(game_state)
    holy_stones = [(pos, type) for pos, type in spoils if type == SpoilType.HOLY_SPIRIT_STONE.value]
    
    if not holy_stones:
        return None
        
    # Find nearest reachable holy stone
    best_path = None
    best_pos = None
    shortest_length = float('inf')
    
    for pos, _ in holy_stones:
        path = find_path_to_position(game_state, my_pos, pos, my_id, phase=2)
        if path and len(path) < shortest_length:
            shortest_length = len(path)
            best_path = path
            best_pos = pos
            
    return best_pos

def find_best_spoil(game_state, my_pos, my_id, player):
    """Find the best spoil to target based on distance and current spoils."""
    spoils = find_spoils(game_state)
    if not spoils:
        return None, None
        
    # Group spoils by their Manhattan distance
    spoils_by_distance = {}
    for spoil_pos, spoil_type in spoils:
        distance = abs(spoil_pos[0] - my_pos[0]) + abs(spoil_pos[1] - my_pos[1])
        if distance not in spoils_by_distance:
            spoils_by_distance[distance] = []
        spoils_by_distance[distance].append((spoil_pos, spoil_type))
    
    # Check spoils starting from nearest
    for distance in sorted(spoils_by_distance.keys()):
        same_distance_spoils = spoils_by_distance[distance]
        
        # Sort spoils at this distance by priority
        prioritized_spoils = sorted(
            same_distance_spoils,
            key=lambda x: get_spoil_priority(x[1], player),
            reverse=True  # Higher priority first
        )
        
        # Try each spoil in priority order
        for spoil_pos, spoil_type in prioritized_spoils:
            path = find_path_to_position(game_state, my_pos, spoil_pos, my_id, phase=2)
            if path:
                logging.info(f"Found {spoil_type} at distance {distance} with counts: "
                           f"sticky_rice={player.sticky_rice}, "
                           f"chung_cake={player.chung_cake}, "
                           f"nine_tusk={player.nine_tusk_elephant}")
                return spoil_pos, path
                
    return None, None

def is_safe_escape_position(game_state, position, my_id, danger_tiles, phase=1):
    """Check if a position is safe to escape to (not cornered and not in danger)."""
    row, col = position
    cell = game_state.map_info.map_matrix[row, col]
    
    # Position should not be in immediate danger
    if position in danger_tiles:
        return False
        
    # Check if the position itself is walkable based on phase
    if phase == 1:
        if cell in [Tile.WALL.value, Tile.BALK.value, Tile.PRISON.value]:
            return False
    else:  # phase 2
        if cell in [Tile.WALL.value, Tile.BALK.value, Tile.BRICK_WALL.value, Tile.PRISON.value]:
            return False
    
    # Count walkable adjacent tiles (need at least 2 for escape route)
    adjacent_positions = [
        (row-1, col),  # up
        (row+1, col),  # down
        (row, col-1),  # left
        (row, col+1)   # right
    ]
    
    walkable_adjacent = 0
    for adj_pos in adjacent_positions:
        adj_row, adj_col = adj_pos
        if (0 <= adj_row < game_state.map_info.map_matrix.rows and
            0 <= adj_col < game_state.map_info.map_matrix.cols):
            adj_cell = game_state.map_info.map_matrix[adj_row, adj_col]
            
            # Check walkability based on phase
            if phase == 1:
                if adj_cell not in [Tile.WALL.value, Tile.BALK.value, Tile.PRISON.value]:
                    walkable_adjacent += 1
            else:  # phase 2
                if adj_cell not in [Tile.WALL.value, Tile.BALK.value, Tile.BRICK_WALL.value, Tile.PRISON.value]:
                    walkable_adjacent += 1
    
    # Need at least 2 walkable adjacent tiles to avoid getting trapped
    return walkable_adjacent >= 2

def get_next_action(game_state, current_pos, next_pos, phase):
    """Convert next position into an action."""
    global faced_wall, standing_on_god
    diff_row = next_pos[0] - current_pos[0]
    diff_col = next_pos[1] - current_pos[1]
    
    try:
        # Check if we're currently on god badge
        current_tile = game_state.map_info.map_matrix[current_pos[0], current_pos[1]]
        if phase == 1 and current_tile == Tile.GOD_BADGE.value:
            standing_on_god = True
            return Drive.STOP.value
            
        next_tile = game_state.map_info.map_matrix[next_pos[0], next_pos[1]]
        
        # Phase 1: Break brick walls on the way to god badge
        if phase == 1 and next_tile == Tile.BRICK_WALL.value:
            if faced_wall:
                faced_wall = False
                return Drive.BOMB.value
            else:
                faced_wall = True
                if diff_row == 1:
                    return Drive.DOWN.value
                elif diff_row == -1:
                    return Drive.UP.value
                elif diff_col == 1:
                    return Drive.RIGHT.value
                elif diff_col == -1:
                    return Drive.LEFT.value
                
        # Phase 2: Bomb balks from any adjacent position
        elif phase == 2 and next_tile == Tile.BALK.value:
            return Drive.BOMB.value
            
        # Normal movement
        standing_on_god = False  # Reset when moving
        faced_wall = False
        if diff_row == 1:
            return Drive.DOWN.value
        elif diff_row == -1:
            return Drive.UP.value
        elif diff_col == 1:
            return Drive.RIGHT.value
        elif diff_col == -1:
            return Drive.LEFT.value
            
    except Exception as e:
        logging.error(f"Error in get_next_action: {e}")
        
    return Drive.STOP.value

def find_nearest_balk_target(game_state, my_player):
    """Find nearest reachable balk."""
    balks = []
    for row in range(game_state.map_info.map_matrix.rows):
        for col in range(game_state.map_info.map_matrix.cols):
            if game_state.map_info.map_matrix[row, col] == Tile.BALK.value:
                balks.append((row, col))
    
    if not balks:
        return None
        
    # Find nearest reachable balk
    best_pos = None
    shortest_length = float('inf')
    
    for balk_pos in balks:
        path = find_path_to_position(game_state, my_player.current_position, balk_pos, my_player.id, phase=2)
        if path and len(path) < shortest_length:
            shortest_length = len(path)
            best_pos = balk_pos
            
    return best_pos

def is_adjacent_to_balk(game_state, position):
    """Check if position is adjacent to a balk."""
    row, col = position
    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        r, c = row + dr, col + dc
        if (0 <= r < game_state.map_info.map_matrix.rows and
            0 <= c < game_state.map_info.map_matrix.cols and
            game_state.map_info.map_matrix[r, c] == Tile.BALK.value):
            return True
    return False

def count_escape_routes(game_state, position, my_id, phase):
    """Count number of possible escape routes from a position."""
    row, col = position
    escape_routes = 0
    
    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        next_pos = (row + dr, col + dc)
        if (0 <= next_pos[0] < game_state.map_info.map_matrix.rows and
            0 <= next_pos[1] < game_state.map_info.map_matrix.cols and
            is_walkable(game_state, next_pos, my_id, phase)):
            escape_routes += 1
            
    return escape_routes

def evaluate_target_value(player):
    """Calculate how valuable a target is based on their state."""
    value = 0
    
    # Transformed players are high value targets
    if player.has_transform:
        value += 100
        
    # Players with spoils are valuable targets
    value += (player.sticky_rice + player.chung_cake + 
             player.nine_tusk_elephant + player.nine_spur_rooster + 
             player.nine_mane_hair_horse) * 20
             
    # Holy stone carriers are highest value
    if player.holy_spirit_stone:
        value += 200
        
    return value

def should_switch_to_attack(game_state, my_player, enemy_value):
    """Determine if we should switch to attack mode."""
    global last_strategy_change, current_strategy
    
    # Don't change strategy too frequently
    if time() - last_strategy_change < STRATEGY_DURATION:
        return current_strategy == 'attack'
    
    # Base weights
    attack_weight = 0
    collect_weight = 0
    
    # Factors favoring attack
    attack_weight += enemy_value * 0.5
    if my_player.power > 2:  # If we have good bomb power
        attack_weight += 30
    if my_player.speed > 2:  # If we have good speed
        attack_weight += 20
        
    # Factors favoring collection
    spoils_count = len(game_state.map_info.spoils)
    collect_weight += spoils_count * 15
    if my_player.power < 2:
        collect_weight += 40
    if my_player.speed < 2:
        collect_weight += 30
        
    # Random factor to break symmetry (10% randomness)
    attack_weight *= random.uniform(0.95, 1.05)
    collect_weight *= random.uniform(0.95, 1.05)
    
    # Update strategy if weights differ significantly
    if abs(attack_weight - collect_weight) > 20:
        new_strategy = 'attack' if attack_weight > collect_weight else 'collect'
        if new_strategy != current_strategy:
            last_strategy_change = time()
            current_strategy = new_strategy
            logging.info(f"Switching strategy to {current_strategy} "
                        f"(attack: {attack_weight:.1f}, collect: {collect_weight:.1f})")
    
    return current_strategy == 'attack'

def is_in_loop(current_pos):
    """Check if we're stuck in a movement loop or stopping."""
    global consecutive_stops
    
    if len(last_positions) >= 4:  # Need at least 4 positions to detect patterns
        # Check if we're stuck in the same position
        if all(pos == current_pos for pos in last_positions[-3:]):
            consecutive_stops += 1
            return True
            
        # Check for oscillating pattern
        if len(set(last_positions[-4:])) <= 2:  # If only moving between 2 positions
            return True
            
        # Check for repeated position pattern
        position_counts = {}
        for pos in last_positions[-6:]:  # Check last 6 positions
            position_counts[pos] = position_counts.get(pos, 0) + 1
            if position_counts[pos] >= 3:  # If we visited same position 3+ times
                return True
                
    return False

def find_bombing_opportunity(game_state, my_player, phase, is_focus_on_enemy = False):
    """Find a good opportunity to bomb an enemy."""
    current_time = time()
    
    # Enforce cooldown between attacks
    if current_time - last_attack_time < ATTACK_COOLDOWN:
        return None, 0
        
    best_target = None
    best_value = 0
    best_bomb_pos = None
    
    for player in game_state.map_info.players:
        if player.id == my_player.id:
            continue
            
        # Simple distance check first
        manhattan_dist = (abs(player.current_position[0] - my_player.current_position[0]) + 
                        abs(player.current_position[1] - my_player.current_position[1]))
                        
        # Only consider nearby enemies if not focusing on enemy
        if manhattan_dist > 4 and is_focus_on_enemy == False:  # Reduced from 5 to 4 for more decisive action
            continue
            
        # Calculate target value
        value = evaluate_target_value(player)
        if value <= 0:
            continue
            
        # Target current position only, no prediction
        target_pos = player.current_position
        
        # Count escape routes
        escape_routes = count_escape_routes(game_state, target_pos, player.id, phase)
        
        # Adjust value based on trappedness
        if escape_routes <= 2:
            value *= (3 - escape_routes)
            
        # Find possible bombing positions
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            bomb_pos = (target_pos[0] + dr, target_pos[1] + dc)
            
            if (0 <= bomb_pos[0] < game_state.map_info.map_matrix.rows and
                0 <= bomb_pos[1] < game_state.map_info.map_matrix.cols and
                is_walkable(game_state, bomb_pos, my_player.id, phase)):
                
                path = find_path_to_position(game_state, my_player.current_position, 
                                          bomb_pos, my_player.id, phase=2)
                                          
                if path and value > best_value:
                    best_target = player
                    best_value = value
                    best_bomb_pos = bomb_pos
    
    logging.info(f"Best bomb target: {best_target.id if best_target else 'None'}, ")
    return best_bomb_pos, best_value

def find_best_god_badge(game_state, my_player):
    """Find the best god badge to target."""
    badges = []
    for badge in get_god_badges(game_state):
        badges.append(badge)
    
    if not badges:
        logging.info("No god badges found")
        return None
        
    # Find nearest reachable badge
    best_pos = None
    shortest_length = float('inf')
    
    for badge_pos in badges:
        path = find_path_to_position(game_state, my_player.current_position, badge_pos, my_player.id, phase=1)
        if path:
            # Calculate actual path length
            path_length = len(path)
            
            # Check if this is the shortest path found
            if path_length < shortest_length:
                shortest_length = path_length
                best_pos = badge_pos
                
    if best_pos:
        logging.info(f"Best god badge found at {best_pos} with path length {shortest_length}")
    else:
        logging.info("No reachable god badges found")
        
    return best_pos

def get_god_badges(game_state):
    god_badges = []
    for i in range(game_state.map_info.map_matrix.rows):
        for j in range(game_state.map_info.map_matrix.cols):
            if game_state.map_info.map_matrix[i, j] == Tile.GOD_BADGE.value:
                god_badges.append((i, j))
    return god_badges

def find_alternative_target(game_state, my_player, current_target):
    """Find an alternative target when stuck in a loop."""
    # List all possible targets (spoils and enemies)
    all_targets = []
    
    # Add spoils as potential targets
    for spoil in game_state.map_info.spoils:
        if spoil.position != current_target:
            all_targets.append((spoil.position, "spoil", evaluate_target_value(spoil)))
    
    # Add enemies as potential targets
    for player in game_state.map_info.players:
        if player.id != my_player.id:
            if player.current_position != current_target:
                value = evaluate_target_value(player)
                all_targets.append((player.current_position, "enemy", value))
    
    # Sort targets by value and distance
    all_targets.sort(key=lambda x: (
        x[2],  # value
        -(abs(x[0][0] - my_player.current_position[0]) +  # negative distance (closer is better)
         abs(x[0][1] - my_player.current_position[1]))
    ), reverse=True)
    
    # Try targets until we find a reachable one with a different path
    for target_pos, target_type, _ in all_targets:
        path = find_path_to_position(game_state, my_player.current_position, 
                                   target_pos, my_player.id, phase=2)
        if path and path[1] not in last_positions[-4:]:  # Ensure new path
            logging.info(f"Found alternative {target_type} target at {target_pos}")
            return target_pos
            
    return None

def find_emergency_move(game_state, my_player, phase):
    """Find any safe move when stuck."""
    current_pos = my_player.current_position
    danger_tiles = get_bomb_danger_tiles(game_state)
    
    # Try all directions in random order
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    random.shuffle(directions)
    
    for dr, dc in directions:
        next_pos = (current_pos[0] + dr, current_pos[1] + dc)
        
        # Check if move is safe and hasn't been recently visited
        if (0 <= next_pos[0] < game_state.map_info.map_matrix.rows and
            0 <= next_pos[1] < game_state.map_info.map_matrix.cols and
            is_walkable(game_state, next_pos, my_player.id, phase) and
            next_pos not in danger_tiles and
            next_pos not in last_positions[-3:]):
            return next_pos
    
    return None

def find_any_valid_target(game_state, my_player):
    """Find any valid target when we have no primary targets."""
    # Try to find nearest breakable object (balk or brick wall)
    nearest_breakable = None
    min_distance = float('inf')
    
    for row in range(game_state.map_info.map_matrix.rows):
        for col in range(game_state.map_info.map_matrix.cols):
            cell = game_state.map_info.map_matrix[row, col]
            pos = (row, col)
            
            # Skip if it's our position
            if pos == my_player.current_position:
                continue
                
            # Check if it's a valid target based on phase
            is_valid_target = False
            if my_player.has_transform:  # Phase 2
                is_valid_target = cell == Tile.BALK.value
            else:  # Phase 1
                is_valid_target = cell == Tile.BRICK_WALL.value
                
            if is_valid_target:
                distance = abs(row - my_player.current_position[0]) + abs(col - my_player.current_position[1])
                if distance < min_distance:
                    path = find_path_to_position(game_state, my_player.current_position, pos, my_player.id, 
                                               phase=2 if my_player.has_transform else 1)
                    if path:
                        min_distance = distance
                        nearest_breakable = pos
    
    return nearest_breakable

def should_collect_spoils(game_state):
    """Determine if we should focus on collecting spoils based on time."""
    global match_start_time
    
    # Initialize start time if not set
    if match_start_time is None:
        match_start_time = time()
        return False
        
    time_elapsed = time() - match_start_time
    logging.info(f"Time elapsed: {int(time_elapsed)}s, Collection ends at: {COLLECTION_PHASE_START}s")
    return time_elapsed < COLLECTION_PHASE_START

def should_wait_after_explosion(game_state, my_pos):
    """Check if we should wait after a bomb explosion."""
    global last_explosion_time
    current_time = int(time() * 1000)  # Current time in milliseconds
    
    # Check for bombs about to explode
    for bomb in game_state.map_info.bombs:
        # Check if bomb is at or adjacent to our position
        if (abs(bomb.position[0] - my_pos[0]) + abs(bomb.position[1] - my_pos[1])) <= 1:
            if bomb.remain_time <= 50:  # If bomb is about to explode
                last_explosion_time = current_time
                logging.info(f"Detected bomb about to explode at {bomb.position}")
                
    # If we recently had an explosion, wait for delay
    if last_explosion_time > 0:
        time_since_explosion = current_time - last_explosion_time
        if time_since_explosion <= EXPLOSION_DELAY:
            logging.info(f"Waiting after explosion, time passed: {time_since_explosion}ms")
            return True
        else:
            last_explosion_time = 0  # Reset timer after delay
        
    return False

def find_nearest_target_phase2(game_state, my_player):
    """Find nearest target in Phase 2, prioritizing spoils over balks."""
    current_pos = my_player.position
    
    # First try to find nearest spoil
    spoils = []
    for row in range(game_state.map_info.map_matrix.rows):
        for col in range(game_state.map_info.map_matrix.cols):
            if game_state.map_info.map_matrix[row, col] == Tile.SPOIL.value:
                spoils.append((row, col))
    
    # If there are spoils, find the nearest one
    if spoils:
        nearest_spoil = None
        shortest_dist = float('inf')
        for pos in spoils:
            dist = abs(pos[0] - current_pos[0]) + abs(pos[1] - current_pos[1])
            if dist < shortest_dist:
                shortest_dist = dist
                nearest_spoil = pos
        return nearest_spoil
        
    # If no spoils, then look for balks
    balks = []
    for row in range(game_state.map_info.map_matrix.rows):
        for col in range(game_state.map_info.map_matrix.cols):
            if game_state.map_info.map_matrix[row, col] == Tile.BALK.value:
                balks.append((row, col))
                
    if balks:
        nearest_balk = None
        shortest_dist = float('inf')
        for pos in balks:
            dist = abs(pos[0] - current_pos[0]) + abs(pos[1] - current_pos[1])
            if dist < shortest_dist:
                shortest_dist = dist
                nearest_balk = pos
        return nearest_balk
        
    return None

def is_within_special_weapon_range(my_pos, target_pos):
    """Check if position is within the 5x area of special weapon effect."""
    row_diff = abs(my_pos[0] - target_pos[0])
    col_diff = abs(my_pos[1] - target_pos[1])
    return row_diff <= 2 and col_diff <= 2

def next_move(game_state: GameStateResponse, my_player: PlayerResponse):
    global last_attack_time, consecutive_stops, move_counter
    
    # Increment move counter
    move_counter += 1
    
    # Update our position history
    current_pos = my_player.current_position
    if not last_positions or current_pos != last_positions[-1]:
        last_positions.append(current_pos)
        if len(last_positions) > POSITION_HISTORY:
            last_positions.pop(0)
    
    phase = 2 if my_player.has_transform else 1
    
    # FIRST PRIORITY: Check for immediate danger
    danger_tiles = get_bomb_danger_tiles(game_state)
    if current_pos in danger_tiles:
        logging.info("In danger! Looking for escape route...")
        escape_path = find_escape_path(game_state, current_pos, danger_tiles, my_player.id, phase)
        if escape_path:
            next_pos = escape_path[0]
            logging.info(f"Escaping to {next_pos}")
            return get_next_action(game_state, current_pos, next_pos, phase)
        else:
            logging.warning("No escape path found!")
    
    # SECOND PRIORITY: Check if we should wait after explosion
    if should_wait_after_explosion(game_state, current_pos):
        return Drive.STOP.value
    
    # Only proceed with other actions if we're safe
    if phase == 2:
        # Only check special weapon usage every SPECIAL_WEAPON_CHECK_INTERVAL moves
        if move_counter >= SPECIAL_WEAPON_CHECK_INTERVAL and my_player.holy_spirit_stone:
            # Reset counter when interval is reached
            move_counter = 0
            
            # Find highest value target
            best_target = None
            best_value = 0
            for player in game_state.map_info.players:
                if player.id != my_player.id:
                    # Only consider targets we're not too close to
                    if not is_within_special_weapon_range(my_player.current_position, player.current_position):
                        value = evaluate_target_value(player)
                        if value > best_value:
                            best_value = value
                            best_target = player
            
            if best_target:
                logging.info(f"Using special weapon on target {best_target.id} with value {best_value}")
                return {
                    'action': Action.USE_WEAPON.value,
                    'payload': {
                        'destination': {
                            'col': best_target.current_position[1],
                            'row': best_target.current_position[0]
                        }
                    }
                }
            else:
                # If we have holy stone but are too close to targets, move away first
                for player in game_state.map_info.players:
                    if player.id != my_player.id and is_within_special_weapon_range(my_player.current_position, player.current_position):
                        # Try to move away from this player
                        for dr, dc in [(0, 2), (2, 0), (0, -2), (-2, 0)]:  # Try moving 2 steps away
                            retreat_pos = (
                                my_player.current_position[0] + dr,
                                my_player.current_position[1] + dc
                            )
                            if (is_walkable(game_state, retreat_pos, my_player.id, phase) and 
                                retreat_pos not in danger_tiles):
                                return get_next_action(game_state, my_player.current_position, retreat_pos, phase)
        
        # Check weapon in phase 2
        if my_player.cur_weapon == Weapon.WOODEN_PESTLE.value:
            logging.info("Phase 2: Currently using pestle - switching to bomb weapon")
            return {
                'action': Action.SWITCH_WEAPON.value
            }
        
        # Time-based strategy
        if should_collect_spoils(game_state):
            # Collection phase logic...
            spoil_pos, path = find_best_spoil(game_state, current_pos, my_player.id, my_player)
            if spoil_pos and path and len(path) > 1:
                # Double check that next move is safe
                next_pos = path[1]
                if next_pos not in danger_tiles:
                    return get_next_action(game_state, current_pos, next_pos, phase)
                
            # Balk breaking phase logic...
            if is_adjacent_to_balk(game_state, current_pos):
                # Make sure bombing won't trap us
                if find_escape_path(game_state, current_pos, get_bomb_danger_tiles(game_state), 
                                  my_player.id, phase):
                    return Drive.BOMB.value
            
            nearest_balk = find_nearest_balk_target(game_state, my_player)

            if nearest_balk:
                path = find_path_to_position(game_state, current_pos, nearest_balk, my_player.id, phase)
                if path and len(path) > 1 and path[1] not in danger_tiles:
                    return get_next_action(game_state, current_pos, path[1], phase)
                
            # Combat opportunities only if safe
            bomb_pos, target_value = find_bombing_opportunity(game_state, my_player, enemy_positions_history)
            
            if bomb_pos and target_value > 100:
                if current_pos == bomb_pos:
                    # Make sure bombing won't trap us
                    future_danger_tiles = get_bomb_danger_tiles(game_state, current_pos)  # Include our potential bomb
                    logging.debug(f'future danger tiles: {future_danger_tiles}')
                    escape_path = find_escape_path(game_state, current_pos, future_danger_tiles, my_player.id, phase)
                    if escape_path:
                        last_attack_time = time()
                        return Drive.BOMB.value
                else:
                    path = find_path_to_position(game_state, current_pos, bomb_pos, my_player.id, phase)
                    if path and len(path) > 1 and path[1] not in danger_tiles:
                        return get_next_action(game_state, current_pos, path[1], phase)
        else:
            logging.info("Phase 2: Focusing on enemy")
            # Combat opportunities only if safe
            bomb_pos, target_value = find_bombing_opportunity(game_state, my_player, enemy_positions_history, is_focus_on_enemy = True)
            
            if bomb_pos and target_value > 100:
                if current_pos == bomb_pos:
                    # Make sure bombing won't trap us
                    future_danger_tiles = get_bomb_danger_tiles(game_state, current_pos)  # Include our potential bomb
                    logging.debug(f'future danger tiles: {future_danger_tiles}')
                    escape_path = find_escape_path(game_state, current_pos, future_danger_tiles, my_player.id, phase)
                    if escape_path:
                        last_attack_time = time()
                        return Drive.BOMB.value
                else:
                    path = find_path_to_position(game_state, current_pos, bomb_pos, my_player.id, phase)
                    if path and len(path) > 1 and path[1] not in danger_tiles:
                        return get_next_action(game_state, current_pos, path[1], phase)
    
    else:  # Phase 1
       # Find and move to nearest god badge
        target_badge = find_best_god_badge(game_state, my_player)
        if target_badge:
            path = find_path_to_position(game_state, current_pos, target_badge, my_player.id, phase=1)
            if path and len(path) > 1:
                return get_next_action(game_state, current_pos, path[1], phase)
            elif path and len(path) == 1:  # We're next to a brick wall
                # Make sure bombing won't trap us
                potential_danger = get_bomb_danger_tiles(game_state)
                if find_escape_path(game_state, current_pos, potential_danger, my_player.id, phase):
                    return Drive.BOMB.value
        
        # If no badge path, try to break nearest brick wall
        any_target = find_any_valid_target(game_state, my_player)
        if any_target:
            path = find_path_to_position(game_state, current_pos, any_target, my_player.id, phase)
            if path and len(path) > 1:
                return get_next_action(game_state, current_pos, path[1], phase)
            elif path and len(path) == 1:  # We're next to the target
                # Make sure bombing won't trap us
                potential_danger = get_bomb_danger_tiles(game_state)
                if find_escape_path(game_state, current_pos, potential_danger, my_player.id, phase):
                    return Drive.BOMB.value
    
    return Drive.STOP.value