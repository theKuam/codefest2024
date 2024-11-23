import heapq
from itertools import count
import logging
from response.game_state_response import GameStateResponse
from collections import defaultdict


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star(start, goal, game_state: GameStateResponse, enemy_location, safe_tiles = None, bomb_impact_list = None):
    if game_state.is_occupied(goal, enemy_location) and not game_state.is_brick_wall(goal) and not game_state.is_balk(goal):
        return None
    if start == goal:
        return None
    open_set = []
    counter = count()
    heapq.heappush(open_set, (0, next(counter), start))  # Initialize heap with (priority, Location)
    came_from = {}

    g_score = defaultdict(lambda: float('inf'))
    f_score = defaultdict(lambda: float('inf'))
    g_score[start] = 0
    f_score[start] = heuristic(start, goal)

    while open_set:
        _, _, current = heapq.heappop(open_set)  # Pop the smallest priority item

        if current == goal:
            return reconstruct_path(came_from, current)

        for neighbor in game_state.get_surrounding_tiles(current):
            if neighbor != goal and game_state.is_occupied(neighbor, enemy_location):
                continue

            tentative_g_score = g_score[current] + move_cost(neighbor, goal, safe_tiles, bomb_impact_list)

            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], next(counter), neighbor))  # Push (priority, Location)

    return None

def a_star_include_brick_wall(start, goal, game_state: GameStateResponse, enemy_location, safe_tiles = None, bomb_impact_list = None):
    if game_state.is_occupied(goal, enemy_location) and not game_state.is_brick_wall(goal) and not game_state.is_balk(goal):
        return None
    if start == goal:
        return None
    open_set = []
    counter = count()
    heapq.heappush(open_set, (0, next(counter), start))  # Initialize heap with (priority, Location)
    came_from = {}

    g_score = defaultdict(lambda: float('inf'))
    f_score = defaultdict(lambda: float('inf'))
    g_score[start] = 0
    f_score[start] = heuristic(start, goal)

    while open_set:
        _, _, current = heapq.heappop(open_set)  # Pop the smallest priority item

        if current == goal:
            return reconstruct_path(came_from, current)

        for neighbor in game_state.get_surrounding_tiles(current):
            if neighbor != goal and (game_state.is_occupied(neighbor, enemy_location) and not game_state.is_brick_wall(neighbor)):
                continue

            tentative_g_score = g_score[current] + move_cost(neighbor, goal, safe_tiles, bomb_impact_list)

            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], next(counter), neighbor))  # Push (priority, Location)

    return None

def reconstruct_path(came_from, current):
    path = []
    index = 0
    while current in came_from:
        path.append(current)
        index += 1
        current = came_from[current]
    path.append(current)  # add the start node
    path.reverse()
    return path

def move_cost(neighbor, goal, safe_tiles, bomb_impact_list = None):
    if safe_tiles:
        for index, safe_tile in enumerate(safe_tiles):
            if safe_tile == neighbor:
                if bomb_impact_list:
                    return min(10, bomb_impact_list[index])
                else:
                    return 1
            elif safe_tile == goal:
                return 1
            else:
                return 10
    return 1

