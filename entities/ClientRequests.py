from dataclasses import dataclass

@dataclass
class ClientRequestCreate:
    Packet:str = "Client Request Create"
    Token:str
    FlagCreateSession:bool
    FlagAvailableSession:bool
    FlagCompletedSession:bool
    Title:str
    QtdOptions:int
    Options:list
    Timeout:str

@dataclass
class ClientRequest:
    Packet:str = "Client Request Create"
    Token:str
    FlagCreateSession:bool
    FlagAvailableSession:bool
    FlagCompletedSession:bool