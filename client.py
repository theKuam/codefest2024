import multiprocessing
import sys
import socketio
import asyncio
import logging
from time import time

import agent
from utils.constants import SocketEvent
from utils.constants import GameTag
from models.game_state import GameStateResponse

# Arguments for game client
base_url = sys.argv[1]  # server url
game_id = sys.argv[2]  # game id
my_player_id = sys.argv[3]  # my player id


start_time = time()
end_time = time()

# Set up logging
logging.basicConfig(
    format='KSKV level=%(levelname)s time=%(asctime)s message="%(message)s"',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Set up socket.io client
sio = socketio.AsyncClient()

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
@sio.on(SocketEvent.JOIN_GAME.value)
async def on_join_game(response):
    logging.info(f'Joined game: {response}')
    # Register character power after joining
    await sio.emit('register character power', {
        'gameId': game_id,
        'type': 1  # Mountain God
    })

# Handle ticktack player event
@sio.on(SocketEvent.TICKTACK_PLAYER.value)
async def on_ticktack_player(response):
    global start_time
    global my_player_id
    my_player_id = my_player_id[:13]
    # logging.debug(f'my_player_id: {my_player_id}')
    try:
        start_time = time()
        game_state = GameStateResponse(response)
        if game_state.tag != GameTag.UPDATE_DATA.value and game_state.player_id != my_player_id:
            return
        my_player = next((p for p in game_state.map_info.players if p.id == my_player_id), None)

        
        logging.debug(f"tag {game_state.tag}")
        if not my_player:
            return
        
        # Alternate between parent and child moves using a simple toggle
        if not hasattr(on_ticktack_player, 'use_parent'):
            on_ticktack_player.use_parent = True
            
        if on_ticktack_player.use_parent:
            next_move = agent.next_move(game_state, my_player)
        else:
            next_move = agent.next_move(game_state, my_player, is_child=True)

        logging.debug(f"next_move {next_move}")
            
        # logging.debug(f'next_move: {next_move}')
        # Toggle for next tick
        on_ticktack_player.use_parent = not on_ticktack_player.use_parent
            
        # Send the move
        if 'action' in next_move:
            await sio.emit(SocketEvent.ACTION.value, next_move)
        else:
            await sio.emit(SocketEvent.DRIVE_PLAYER.value, next_move)
                
    except Exception as e:
        logging.error(f"Error in ticktack handler: {str(e)}")

@sio.on(SocketEvent.DRIVE_PLAYER.value)
async def on_drive_player(response):
    global end_time
    end_time = time()


async def join_game():
    # Connect to server
    await sio.connect(str(base_url), transports=['websocket'])
    
    # Join game
    await sio.emit(SocketEvent.JOIN_GAME.value, {
        'game_id': game_id,
        'player_id': my_player_id
    })
    
    # Keep connection alive
    while True:
        await asyncio.sleep(1)

def run_client():
    player_id = my_player_id[:13]
    # logging.debug(f'player_id: {player_id}')
    asyncio.run(join_game())

if __name__ == '__main__':
    process = multiprocessing.Process(target=run_client)
    process.start()
    
    try:
        process.join()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Stopping clients...")
        process.terminate()