import asyncio
import websockets
import json

game_state = {
    'board': [['' for _ in range(5)] for _ in range(5)],  # 5x5 board
    'turn': 'Player1',  # 'Player1' or 'Player2'
    'players': {}  # Keeps track of connected players
}

async def update_state(websocket, move_data):
    x, y, player = move_data['x'], move_data['y'], move_data['player']

    if game_state['turn'] == player and game_state['board'][x][y] == '':
        game_state['board'][x][y] = player
        game_state['turn'] = 'Player2' if player == 'Player1' else 'Player1'
        await broadcast_state()
    else:
        await websocket.send(json.dumps({'error': 'Invalid move or not your turn'}))

async def broadcast_state():
    # Only broadcast if two players are connected
    if len(game_state['players']) == 2:
        message = json.dumps({'type': 'update', 'state': game_state})
        await asyncio.wait([player.send(message) for player in game_state['players'].values()])

async def handler(websocket, path):
    player_name = await websocket.recv()  # Receive the player's name upon connection
    game_state['players'][player_name] = websocket  # Add the player to the list of connected players

    try:
        await broadcast_state()  # Send initial game state to all connected players

        async for message in websocket:
            move_data = json.loads(message)
            await update_state(websocket, move_data)

    finally:
        del game_state['players'][player_name]  # Remove player on disconnect
        await broadcast_state()  # Update game state for remaining players

start_server = websockets.serve(handler, "localhost", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
