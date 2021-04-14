from dataclasses import dataclass

@dataclass
class SessionDetails:
    Packet:str = "Session Details"
    Token:str = None
    Title:str = None

@dataclass
class SessionDescription:
    Packet:str = "Session Description"
    Token:str = None
    Title:str = None
    FlagFinished:bool = None
    QtdOptions:int = None
    Result:list = None
    Options:list = None
    Win_tie:list = None