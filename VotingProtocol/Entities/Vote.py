from dataclasses import dataclass

@dataclass
class Vote:
    Packet:str = "Vote"
    Token:str = None
    Title:str = None
    Option:str = None
