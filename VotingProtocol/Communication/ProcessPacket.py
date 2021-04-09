from VotingProtocol.Entities import *
import json
import sys
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

class ProcessPacket:
    def __init__(self, initialEncryption = 'AES', previousRSAKeys = None):
        f = open('VotingProtocol\\config\\AESKey.bin', 'rb')
        self.AESKey = f.read()
        self.Encrypter = initialEncryption
        f.close()

        # RSA encryption
        if previousRSAKeys is not None:
            self.RSALocalPrivateKey = previousRSAKeys
            self.RSALocalPublicKey = self.RSALocalPrivateKey.public_key()
        else:
            self.RSALocalPrivateKey = rsa.generate_private_key(public_exponent=65537, key_size=4096)
            self.RSALocalPublicKey = self.RSALocalPrivateKey.public_key()
        
        self.RSARemotePublicKey = None

    def getLocalPublicKey(self):
        return self.RSALocalPublicKey.public_bytes(encoding=serialization.Encoding.PEM, 
                    format=serialization.PublicFormat.SubjectPublicKeyInfo).decode('utf-8')
    
    def getRemotePublicKey(self):
        if self.RSARemotePublicKey is None:
            return None

        return self.RSARemotePublicKey.public_bytes(encoding=serialization.Encoding.PEM, 
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
            AEScipher = AES.new(self.AESKey, AES.MODE_EAX)
            ciphertext, tag = AEScipher.encrypt_and_digest(strObjbytes)
            encode = {'nonce':AEScipher.nonce.hex(), 'tag':tag.hex(), 'cicherText':ciphertext.hex()}
            cipherObj = json.dumps(encode)
            return cipherObj.encode('utf-8')
        else:
            return self.RSARemotePublicKey.encrypt(strObjbytes, 
                padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
        
    def decode(self, obj, typeObject):
        try:
            if self.Encrypter == 'AES' :
                cipherObj = json.loads(obj.decode('utf-8'))
                nonce = bytes.fromhex(cipherObj['nonce'])
                tag = bytes.fromhex(cipherObj['tag'])
                ciphertext = bytes.fromhex(cipherObj['cicherText'])
                AEScipher = AES.new(self.AESKey, AES.MODE_EAX, nonce)
                strObjbytes = AEScipher.decrypt_and_verify(ciphertext, tag)
            else:
                strObjbytes = self.RSALocalPrivateKey.decrypt(obj, 
                    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(), label=None))
        except Exception as e:
            print(obj)
            print(e)
            return None

        strObj = strObjbytes.decode('utf-8')
        jsonObj = json.loads(strObj)
        if typeObject is not None:
            try:
                typeRef = typeObject()
                ansObj = typeObject(**jsonObj)
                if(typeRef.Packet != ansObj.Packet):
                    return None
                return ansObj
            except Exception:
                return None
        else:
            return jsonObj
