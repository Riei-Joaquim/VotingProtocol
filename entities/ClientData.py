from dataclasses import dataclass

@dataclass
class ClientData:
    Packet:str = "Client Data"
    Email:str
    Password:str
    PublicKey:str
