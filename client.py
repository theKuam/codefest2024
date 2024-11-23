import multiprocessing
import sys
import threading
import time
import socketio
import asyncio
import logging

import agent
from requests.playerActionRequest import PlayerActionRequest
from requests.player_drive_request import PlayerDriveRequest
from response.game_state_response import GameStateResponse
from response.player_resonse import PlayerResponse
import utils.constants as constants
from requests.game_join_request import GameJoiningRequest

# Arguments for game client
base_url = sys.argv[1]  # server url
game_id = sys.argv[2]  # game id
my_player_id = sys.argv[3] # my player id

# Set up logging
logging.basicConfig(
    format='KSKV level=%(levelname)s time=%(asctime)s message="%(message)s"',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Set up socket.io client
sio = socketio.AsyncClient()

current_my_bomb_location = None
current_path = None
current_target = None
current_drive = None
player_position = None
last_handled_time = 0

# Handle connecting to server
@sio.event
async def on_connect():
    logging.info('Connected to server')

# Handle disconnecting from server
@sio.event
async def on_disconnect():
    logging.info('Disconnected from server')

# Handle connection error
@sio.event
async def on_connect_error(data):
    logging.error(f'Failed to connect to server: {data}')

# Handle joining game
@sio.on(constants.SocketEvent.JOIN_GAME.value)
async def on_join_game(response):
    logging.info(f'Joined game: {response}')

# handle ticktack player event
@sio.on(constants.SocketEvent.TICKTACK_PLAYER.value)
async def on_ticktack_player(response):
    global current_my_bomb_location
    global current_path
    global current_target
    global current_drive
    global player_position
    global once_per_half_second
    global last_handled_time

    game_state = GameStateResponse(
        response.get(GameStateResponse.ID),
        response.get(GameStateResponse.TIMESTAMP),
        response.get(GameStateResponse.MAP_INFO),
        response.get(GameStateResponse.TAG),
        response.get(GameStateResponse.PLAYER_ID),
        response.get(GameStateResponse.GAME_REMAIN_TIME),
    )

    my_player_state = agent.get_my_player_state(
        game_state, 
        my_player_id,
    )

    enemy_state = agent.get_enemy_state(
        game_state,
        my_player_id,
    )

    if not player_position == my_player_state.currentPosition:
        player_position = my_player_state.currentPosition
    (path, player_drive, target, is_brick_wall), is_bomb_phase, phase = agent.next_move(
        game_state,
        my_player_state,
        current_my_bomb_location,
    )

    if game_state.tag == constants.GameTag.BOMB_SETUP.value and game_state.player_id == my_player_id:
        current_my_bomb_location = my_player_state.currentPosition

    if game_state.tag == constants.GameTag.BOMB_EXPLODED.value and game_state.player_id == my_player_id:
        current_my_bomb_location = None

    if (
        current_path == None
        or current_target == None or (
            game_state.player_id == my_player_id and (
        game_state.tag == constants.GameTag.START_GAME.value 
        or game_state.tag == constants.GameTag.BOMB_SETUP.value 
        or game_state.tag == constants.GameTag.PLAYER_STOP_MOVING.value
        or game_state.tag == constants.GameTag.BOMB_EXPLODED.value
        or game_state.tag == constants.GameTag.WOODEN_PESTLE_SETUP.value
        or game_state.tag == constants.GameTag.PLAYER_STUN_TIMEOUT.value
        or game_state.tag == constants.GameTag.PLAYER_BACK_TO_PLAYGROUND.value
        )
        )
         ):
        current_path = path
        current_target = target
        current_drive = player_drive

    elif current_path != None and current_target != None and target != None:
        if (current_target == my_player_state.currentPosition or
            (is_brick_wall and (tile == my_player_state.currentPosition for tile in game_state.get_surrounding_tiles(current_target)))):
            current_path = path
            current_target = target
            current_drive = player_drive
        else: 
            return

    if len(current_drive) > 0:
        logging.debug(f'path {current_path}')
        if (last_handled_time == 20):
            logging.debug(f'time {last_handled_time}')
            # await sio.disconnect()
        last_handled_time += 1
        await sio.emit(
                constants.SocketEvent.DRIVE_PLAYER.value,
                PlayerDriveRequest(current_drive).getPlayerDriveRequest(),
            )
    if is_brick_wall:
            if (phase == constants.Phase.PHASE_2 and my_player_state.curWeapon == constants.Weapon.WOODEN_PESTLE.value):
                logging.info('Switching weapon')
                await sio.emit(
                    constants.SocketEvent.ACTION.value,
                    PlayerActionRequest(constants.Action.SWITCH_WEAPON.value).getPlayerActionRequest(),
                )
            await sio.emit(
                constants.SocketEvent.DRIVE_PLAYER.value,
                PlayerDriveRequest(constants.Drive.BOMB.value).getPlayerDriveRequest(),
            )

        # await sio.disconnect()

async def join_game():
    # Request to connect to server
    await sio.connect(str(base_url), transports=['websocket'])

    # Request to join game
    await sio.emit(
            constants.SocketEvent.JOIN_GAME.value,
            GameJoiningRequest(game_id, my_player_id).getGameJoiningRequest(),
        )
    await sio.wait()

def run_client():
    asyncio.run(join_game())

if __name__ == '__main__':
    process = multiprocessing.Process(target=run_client)

    process.start()

    try:
        process.join()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Stopping clients...")
        process.terminate()