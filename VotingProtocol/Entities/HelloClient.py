from dataclasses import dataclass

@dataclass
class HelloClient:
    Packet:str = "Hello Client"
    ServerAddress:str = None
    PublicKey:str = None