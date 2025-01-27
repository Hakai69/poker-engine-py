from enum import Flag, auto

class ClientProtocol(Flag):
    EXIT = auto()
    LIST_ROOMS = auto()
    UPDATE_NAME = auto()
    
    CREATE_ROOM = auto()
    JOIN_ROOM = auto()
    LEAVE_ROOM = auto()
    READY = auto()
    UNREADY = auto()
        
    GAME_ACTION = auto()
    LEAVE_GAME = auto()
    
class ServerProtocol(Flag):
    GAME_MESSAGE = auto()
    
    SUCCESS = auto()
    
    WRONG_VERSION = auto()
    INVALID_ACTION = auto()
    
ClientProtocol.version = '1.0'
ServerProtocol.version = '1.0'