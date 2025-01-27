# Disclaimer: This code is intented for low-scale use. It is not optimized for 
# high performance. It does not use any kind of database, it does not use the 
# best data structures for each job, etc.

# Clients may close

import socket
import threading
import json
import time
from queue import Queue
from typing import Callable, Any

from protocol import ClientProtocol, ServerProtocol
from game import Game
from player import OnlinePlayer



IN_GAME_REQUIRED = \
    ClientProtocol.GAME_ACTION | ClientProtocol.LEAVE_GAME
    
# Allow exit from in-game for correct handling
IN_GAME_ALLOWED = \
    IN_GAME_REQUIRED | ClientProtocol.EXIT

IN_ROOM_REQUIRED = \
    ClientProtocol.LEAVE_ROOM | ClientProtocol.READY | ClientProtocol.UNREADY
    
IN_ROOM_ALLOWED = \
    IN_ROOM_REQUIRED | IN_GAME_ALLOWED



MIN_NAME_LENGTH = 3
MAX_NAME_LENGTH = 20

MIN_PASSWORD_LENGTH = 3
MAX_PASSWORD_LENGTH = 20

class ClientRecord:
    def __init__(
        self,
        socket: socket.socket,
        name: str,
    ):
        self.socket = socket
        self.username = name
        self.room: Room | None = None
        self.game: Game | None = None
        self.player: OnlinePlayer = None
        
    def in_room(self):
        return self.room is not None
    
    def in_game(self):
        if self.game is None:
            return False
        
        if self.game.is_finished():
            self.game = None
            return False
        
        return True
    
    
class Room[Client]:
    def __init__(self, name: str, clients: list[Client], password: str | None = None):
        self.name = name
        self.clients = clients
        self.ready: list[Client] = []
        self.password = password
        self.game: Game | None = None
    
    def is_private(self):
        return bool(self.password)
    
    def is_public(self):
        return not self.is_private()
    
    def is_empty(self):
        return not bool(self.clients)

class Server:

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 12345,
        max_players: int | None = None,
    ):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(4)
                
        self.max_players = max_players
        self.clients: dict[socket.socket, ClientRecord] = dict()
        # Player -> Client
        self.players: dict[socket.socket, socket.socket] = dict()
        self.rooms: dict[str, Room[ClientRecord]] = dict()
        self.usernames: set[str] = set()
        
            
    def start(self):
        '''
        Run the server.
        '''
        
        print("Server is running...")
        try:
            while True:
                if self.max_players and len(self.clients) == self.max_players:
                    time.sleep(1)
                    continue
                
                client_socket, addr = self.server_socket.accept()
                
                print(f"Connection from {addr}")
                threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,)
                ).start()
                
        except Exception as e:
            print(f"Error running server: {e}")
        finally:
            self.server_socket.close()
            print("Server closed.")


    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(message)
            except Exception as e:
                print(f"Error sending message to client: {e}")
                self.clients.remove(client)


    def send_private_message(self, client_socket: socket.socket, message):
        try:
            client_socket.send(message)
        except Exception as e:
            print(f"Error sending private message to client: {e}")
            self.clients.remove(client_socket)


    def handle_client(self, client_socket: socket.socket):
        '''
        Manage a new client's connection.
        
        Args
        -----
            client_socket: socket
                The client's socket.
        '''
        
        username = f'user_{len(self.clients)}'
        i = 1
        while username in self.usernames:
            # Fill in the blanks
            username = f'user_{len(self.clients) - i}'
            i += 1
                        
        self.usernames.add(username)
        self.clients[client_socket] = ClientRecord(client_socket, username)
        
        try:
            while True:
                data = client_socket.recv(1024).decode()
                self.process_client_message(client_socket, data.strip())
                    
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()
            self.clients.remove(client_socket)


    def process_client_message(self, client_socket: socket.socket, message: str):
        '''
        Verify the message from the client and execute the corresponding 
        routine given the message from the client.
        
        Args:
            client_socket: socket
                The client's socket.
            message: str
                The message sent by the client.
        '''
        
        data: dict = json.loads(message)
        client = self.clients[client_socket]
        
        # Check the version
        version = data.get('protocol_version')
        if version != ClientProtocol.version:
            response = {
                'action': ClientProtocol.WRONG_VERSION.value,
                'protocol_version': ServerProtocol.version,
                'value': f'Expected version {ClientProtocol.version}, given {version}.'
            }
            client_socket.sendall(json.dumps(response).encode())
            return
        
        # Retrieve the action
        try:
            try:
                action = ClientProtocol(data.get('action'))
            except ValueError:
                raise ValueError('Unknown action provided.')
            
            in_game = client.in_game()
            if in_game and not action & IN_GAME_ALLOWED:
                raise ValueError('You must leave the game to perform this action.')
            if not in_game and action & IN_GAME_REQUIRED:
                raise ValueError('You must be in-game to perform this action.')
            
            in_room = client.in_room()
            if in_room and not action & IN_ROOM_ALLOWED:
                raise ValueError('You must leave the room to perform this action.')
            if not in_room and action & IN_ROOM_REQUIRED:
                raise ValueError('You must be in a room to perform this action.')

            
        except ValueError as e:
            response = {
                'action': ServerProtocol.INVALID_ACTION.value,
                'protocol_version': ServerProtocol.version,
                'value': str(e),
            }
            if action: response['client_action'] = action.value
            
            client_socket.sendall(json.dumps(response).encode())
            return
        
        params = data.get('params')
        action_method = Server.action_to_method.get(action)
        try:
            data = action_method(
                self, 
                client_socket = client_socket,
                params = params
            )
            response = {
                'action': ServerProtocol.SUCCESS.value,
                'protocol_version': ServerProtocol.version,
                'client_action': action.value,
            }
            if data:
                response['value'] = data
                
        except Exception as e:
            response = {
                'action': ServerProtocol.INVALID_ACTION.value,
                'protocol_version': ServerProtocol.version,
                'client_action': action.value,
                'value': str(e),
            }
        
        client_socket.sendall(json.dumps(response).encode())
        
    # ACTION METHODS
    def list_rooms(
        self,
        *,
        client_socket = None,
        params: dict
    ) -> list[dict]:
        '''
        Retrieve all the rooms in the server given some basic query parameters.
        
        Args
        -----
            client_socket
                Will not be used.
            params: dict
                Basic query system.
        
        Params
        -------
            private: bool
                Whether it should list private or public rooms. By default it 
                lists all rooms.
            include_full: bool, default=False
                Whether it should include full rooms.
            
        Returns
        --------
            rooms: list[dict]
                A list of with dictionary representations of rooms, which have 
                the room's name, whether it is private or not, and the number 
                of players inside it.
        '''
        
        rooms = []
        checks = [lambda room: len(room.clients) < 2]
        if params:
            if 'include_full' in params and params['include_full']:
                checks.pop()
            if 'private' in params:
                if params['privacy']:
                    checks.append(lambda room: room.is_private())
                else:
                    checks.append(lambda room: room.is_public())
                
        def perform_checks(room):
            for check in checks:
                if not check(room):
                    return False
            return True
                
        for room_name, room in self.rooms.items():
            if not perform_checks(room):
                continue
            
            private_room = room.is_private()
            rooms.append({
                'name': room_name,
                'private': private_room,
                'players': len(room.clients)
            })

        return rooms
    
    
    def update_name(
        self,
        *,
        client_socket: socket.socket, 
        params: dict
    ):
        '''
        Change the client's name to a new name.
        
        Args
        -----
            client_socket: socket
                The client's socket.
            params: dict
                Specific parameters for the action.
        
        Params
        -------
            name: str
                The new username.
        '''
        
        if not params or 'name' not in params:
            raise ValueError('You must provide a new name.')
        
        new_name = params.get('name')
        if not isinstance(new_name, str):
            raise ValueError('Name must be a string.')
        
        if not MIN_NAME_LENGTH < len(new_name) < MAX_NAME_LENGTH:
            raise ValueError(
                'Name must be between '
                f'{MIN_NAME_LENGTH} and {MAX_NAME_LENGTH} characters.'
            )
        
        client = self.clients[client_socket]
        self.usernames.remove(client.username)
        self.usernames.add(new_name)
        client.username = new_name
        
        
    def create_room(
        self,
        *,
        client_socket: socket.socket,
        params: dict
    ):
        '''
        Instantiate a new a room with the client in it.
        
        Args
        -----
            client_socket: socket
                The client's socket.
            params: dict
                Specific parameters for the action.
                
        Params
        -------
            name: str
                The room's name.
            password: str
                The room's password. Optional.
        '''
        
        if not params or 'name' not in params:
            raise ValueError('You must provide a room name.')
        
        room_name = params.get('name')
        if room_name in self.rooms:
            raise ValueError('Room already exists.')
        
        if not isinstance(room_name, str):
            raise ValueError('Room name must be a string.')
        
        if not room_name.isalnum():
            raise ValueError(
                f'Room name must be alphanumeric. Name provided: {room_name}.'
            )
        
        if not MIN_NAME_LENGTH < len(room_name) < MAX_NAME_LENGTH:
            raise ValueError(
                'Room name must be between '
                f'{MIN_NAME_LENGTH} and {MAX_NAME_LENGTH} characters.'
            )
        
        client = self.clients[client_socket]
        
        # Explicitely set to None if not provided
        password = params.get('password', None)
        
        if password:
            if not isinstance(password, str):
                raise ValueError('Room password must be a string.')
            if not MIN_PASSWORD_LENGTH < len(password) < MAX_PASSWORD_LENGTH:
                raise ValueError(
                    'Room password must be between '
                    f'{MIN_PASSWORD_LENGTH} and {MAX_PASSWORD_LENGTH} characters.'
                )
        
        self.rooms[room_name] = Room(room_name, [client], password)
        client.room = room_name
        
    
    def join_room(
        self,
        *,
        client_socket: socket.socket,
        params: dict
    ):
        '''
        Insert the client into a given room.
        
        Args
        -----
            client_socket: socket
                The client's socket.
            params: dict
                Specific parameters for the action.
            
        Params
        -------
            name: str
                The room's name.
            password: str
                The room's password. Optional.
        '''
        
        if not params or 'name' not in params:
            raise ValueError('You must provide a room name.')
        
        room_name = params.get('name')
        if not isinstance(room_name, str):
            raise ValueError('Room name must be a string.')
        
        if room_name not in self.rooms:
            raise ValueError('Room does not exist.')
        
        room = self.rooms[room_name]
        
        if len(room.clients) >= 2:
            raise ValueError('Room is full.')
        
        if room.password and room.password != params.get('password'):
            raise ValueError('Wrong password.')
        
        client = self.clients[client_socket]
        room.clients.append(client)
        client.room = room_name
        
        
    def leave_room(
        self,
        *,
        client_socket: socket.socket,
        params = None
    ):
        '''
        Remove the client from their room.
        
        Args
        -----
            client_socket: socket
                The client's socket.
            params
                No parameters needed. Will be ignored.
        '''
        
        client = self.clients[client_socket]
        room_name = client.room
        room = self.rooms[room_name]
        room.clients.remove(client)
        client.room = None
        
        if room.is_empty():
            del self.rooms[room_name]
            
            
    def ready(
        self,
        *,
        client_socket: socket.socket,
        params = None
    ):
        '''
        Mark the client as ready to start the game. If both clients are ready, 
        the game will start.
        
        Args
        -----
            client_socket: socket
                The client's socket.
            params
                No parameters needed. Will be ignored.
        '''
        
        client = self.clients[client_socket]
        room_name = client.room
        room = self.rooms[room_name]
        
        if client in room.ready:
            raise ValueError('You are already ready.')
        
        room.ready.append(client)
        if len(room.ready) == 2:
            players = []
            for client in room.ready:
                client.game = room.game
                server_queue = Queue()
                client.player = OnlinePlayer(client.username, server_queue)
                                
                threading.Thread(
                    target=self.handle_player,
                    args=(client_socket, server_queue)
                ).start()
                players.append(client.player)
                
            
            room.game = Game(room.clients, *players)
            threading.Thread(target=room.game.start).start()
            
            # Reset room
            room.ready = []
            
    
    def unready(
        self,
        *,
        client_socket: socket.socket,
        params = None
    ):
        '''
        Mark the client as not ready to start the game.
        
        Args
        -----
            client_socket: socket
                The client's socket.
            params
                No parameters needed. Will be ignored.
        '''
        
        client = self.clients[client_socket]
        room_name = client.room
        room = self.rooms[room_name]
        
        if client not in room.ready:
            raise ValueError('You are already not ready.')
        
        room.ready.remove(client)
        
    
    def game_action(
        self,
        *,
        client_socket: socket.socket,

        params: dict
    ):
        '''
        Play the client's game action.
        
        Args
        -----
            client_socket: socket
                The client's socket.
            params: dict
                Data to be sent to the player.
        '''
        
        client = self.clients[client_socket]
        if not params:
            raise ValueError('You must provide a game action.')
        
        client.player.queue.put(params)
        
    
    def leave_game(
        self,
        *,
        client_socket: socket.socket,
        params = None,
    ):

        '''
        Remove the client from the game.
        
        Args
        -----
            client_socket: socket
                The client's socket.
            params
                No parameters needed. Will be ignored.
        '''
        
        # The game thread is running asynchronously, so we will need to set a 
        # flag and the game will finish eventually.
        client = self.clients[client_socket]
        client.player.exit()
        
        # client.game will also be updated eventually
        
        
    def exit(
        self,
        *,
        client_socket: socket.socket,
        params = None
    ):
        '''
        Force exit client from the server.
        
        Args
        -----
            client_socket: socket
                The client's TCP socket.
            params
                No parameters needed. Will be ignored.
        '''
        
        client = self.clients[client_socket]
        if client.in_game():
            self.leave_game(client_socket=client_socket)
                        
        if client.in_room():
            self.leave_room(client_socket=client_socket)
            
            
        del self.clients[client_socket]
        self.usernames.remove(client.username)
        client_socket.close()
        
        
    # PLAYERS      
    def handle_player(
        self,
        client_socket: socket.socket,
        server_queue: Queue
    ):
        '''
        Manage the player's messages.
        
        Args
        -----
            client_socket: socket
                The client's socket.
            server_queue: Queue
                The queue to receive messages from the player.
        '''
        
        client = self.clients[client_socket]
        while client.in_game():
            data = server_queue.get().decode()
            self.route_player_message(client_socket, data.strip())

            
    def route_player_message(self, client_socket: socket.socket, message: str):
        '''
        Send player's messages to the client.
        
        Args
        -----
            client_socket: socket
                The socket of the corresponding client.
            message: str
                The data desired to be sent.
        '''
        data: dict = json.loads(message)
        
        # Encapsulate the data
        response = {
            'action': ServerProtocol.GAME_MESSAGE.value,
            'protocol_version': ServerProtocol.version,
            'value': data
        }
        
        client_socket.sendall(response)    
                
            
action_to_method: dict[
    ClientProtocol,
    Callable[
        [
            Server,
            socket.socket | None,
            dict | None
        ],
        Any
    ]
] = {
    ClientProtocol.LIST_ROOMS: Server.list_rooms,
    ClientProtocol.UPDATE_NAME: Server.update_name,
    ClientProtocol.CREATE_ROOM: Server.create_room,
    ClientProtocol.JOIN_ROOM: Server.join_room,
    ClientProtocol.LEAVE_ROOM: Server.leave_room,
    ClientProtocol.READY: Server.ready,
    ClientProtocol.UNREADY: Server.unready,
    ClientProtocol.EXIT: Server.exit,
    ClientProtocol.GAME_ACTION: Server.game_action,
    ClientProtocol.LEAVE_GAME: Server.leave_game,
}
Server.action_to_method = action_to_method

if __name__ == "__main__":
    server = Server()
    server.start()