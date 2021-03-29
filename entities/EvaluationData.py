from dataclasses import dataclass

@dataclass
class EvaluationData:
    Packet:str = "Evaluation Data"
    FlagAutentication:bool
    Token:str
