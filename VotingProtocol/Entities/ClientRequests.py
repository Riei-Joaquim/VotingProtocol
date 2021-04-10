from dataclasses import dataclass

@dataclass
class ClientRequestCreate:
    Packet:str = "Client Request Create"
    Token:str = None
    FlagCreateSession:bool = None
    FlagAvailableSession:bool = None
    FlagCompletedSession:bool = None
    Title:str = None
    QtdOptions:int = None
    Options:list = None
    Timeout:str = None

@dataclass
class ClientRequest:
    Packet:str = "Client Request"
    Token:str = None
    FlagCreateSession:bool = None
    FlagAvailableSession:bool = None
    FlagCompletedSession:bool = None