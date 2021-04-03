from dataclasses import dataclass

@dataclass
class EvaluationData:
    Packet:str = "Evaluation Data"
    FlagAutentication:bool = None
    Token:str = None