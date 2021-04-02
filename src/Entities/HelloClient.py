from dataclasses import dataclass

@dataclass
class HelloClient:
    Packet:str = "Hello Client"
    ServerAddress:str
    PublicKey:str