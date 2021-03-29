from dataclasses import dataclass

@dataclass
class RequestResponse:
    Packet:str = "Request Response"
    FlagAvailableSessions:bool
    FlagCompletedSessions:bool
    QtdSessions:int
    Sessions:list
