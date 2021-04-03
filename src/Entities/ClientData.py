from dataclasses import dataclass

@dataclass
class ClientData:
    Packet:str = "Client Data"
    Email:str = None
    Password:str = None
    PublicKey:str = None
