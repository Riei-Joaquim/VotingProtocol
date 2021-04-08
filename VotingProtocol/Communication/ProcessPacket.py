from VotingProtocol.Entities import *
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

class ProcessPacket:
    def __init__(self):
        f = open('VotingProtocol\\config\\AESKey.bin', 'rb')
        self.AESKey = f.read()
        self.Encrypter = 'AES'
        f.close()
        # AES encryption
        self.AEScipher = Fernet(self.AESKey)
        # RSA encryption
        self.RSALocalPrivateKey = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.RSALocalPublicKey = self.RSALocalPrivateKey.public_key()
        self.RSARemotePublicKey = ''

    def getLocalPublicKey(self):
        return self.RSALocalPublicKey.public_bytes(encoding=serialization.Encoding.PEM, 
                    format=serialization.PublicFormat.SubjectPublicKeyInfo).decode('utf-8')

    def setRemotePublicKey(self, remotePublicKey):
        key = serialization.load_pem_public_key(remotePublicKey.encode())
        if isinstance(key, rsa.RSAPublicKey):
            self.RSARemotePublicKey = key
            self.Encrypter = 'RSA'
        else:
            print('Invalid Public Key!')

    def encode(self, obj):
        strObj = json.dumps(obj.__dict__)
        strObjbytes = strObj.encode('utf-8')

        if(self.Encrypter == 'AES'):
            return self.AEScipher.encrypt(strObjbytes)
        else:
            return self.RSARemotePublicKey.encrypt(strObjbytes, 
                padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
        
    def decode(self, obj):
        if self.Encrypter == 'AES' :
            strObjbytes = self.AEScipher.decrypt(obj)
        else:
            strObjbytes = self.RSALocalPrivateKey.decrypt(obj, 
                padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(), label=None))

        strObj = strObjbytes.decode('utf-8')
        jsonObj = json.loads(strObj)
        return jsonObj