from dataclasses import dataclass

@dataclass
class Vote:
    Packet:str = "Vote"
    Token:str
    Title:str
    Options:str
