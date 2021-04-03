from dataclasses import dataclass

@dataclass
class FinishConnection:
    Packet:str = "Finish Connection"
    Token:str = None