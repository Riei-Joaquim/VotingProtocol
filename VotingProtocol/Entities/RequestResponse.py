from dataclasses import dataclass

@dataclass
class RequestResponse:
    Packet:str = "Request Response"
    FlagAvailableSessions:bool = None
    FlagCompletedSessions:bool = None
    FlagCreatedSessions:bool = None
    QtdSessions:int = None
    Sessions:list = None
