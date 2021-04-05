from dataclasses import dataclass

@dataclass
class VoteResponse:
    Packet:str = "Vote Response"
    Title:str = None
    Options:str = None
    FlagComputed:bool = None
    Description:str = None