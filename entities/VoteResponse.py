from dataclasses import dataclass

@dataclass
class VoteResponse:
    Packet:str = "Vote Response"
    Title:str
    Options:str
    FlagComputed:bool
    Description:str
