from dataclasses import dataclass

@dataclass
class SessionDetails:
    Packet:str = "Session Details"
    Token:str
    Title:str

@dataclass
class SessionDescription:
    Packet:str = "Session Description"
    Token:str
    Title:str
    FlagFinished:bool
    QtdOptions:int
    Result:list
    Options:list
