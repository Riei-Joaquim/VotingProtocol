from VotingProtocol.Entities import *
import json
import sys
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import utils
from cryptography.exceptions import InvalidSignature
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
    
    def segmentPacket(self, strObj, blockSize):
        blocksList = {}
        block = strObj[0]
        segment = 0

        for i in range(1, len(strObj)):
            if i% blockSize == 0:
                blocksList[str(segment)] = block
                segment += 1
                block = ''
            block += strObj[i]

            if i == (len(strObj) -1):
                blocksList[str(segment)] = block
        
        return blocksList
    
    def signAESPacket(self, packetBytes, key):
        RSASignPrivateKey = serialization.load_pem_private_key(key, password=None)
        hasher = hashes.Hash(hashes.SHA256())
        hasher.update(packetBytes)
        digest = hasher.finalize()
        signature = RSASignPrivateKey.sign(
            digest,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=padding.PSS.MAX_LENGTH),
            utils.Prehashed(hashes.SHA256()))
        packet = {'payload': packetBytes.hex(), 'sign':signature.hex()}
        cipherObj = json.dumps(packet)

        return cipherObj.encode('utf-8')
    
    def verifySignAESPacket(self, packetBytes, key):
        try:
            cipherObj = json.loads(packetBytes.decode('utf-8'))
            payload = bytes.fromhex(cipherObj['payload'])
            sign = bytes.fromhex(cipherObj['sign'])
            RSASignPublicKey = serialization.load_pem_public_key(key)
        except Exception as e:
            print(packetBytes)
            print(e)
            return None

        try:
            hasher = hashes.Hash(hashes.SHA256())
            hasher.update(payload)
            digest = hasher.finalize()
            RSASignPublicKey.verify(
                sign,
                digest,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                utils.Prehashed(hashes.SHA256()))
        except InvalidSignature as e:
            print(e)
            return None

        return payload

    def encode(self, obj):
        strObj = json.dumps(obj.__dict__)
        
        if(self.Encrypter == 'AES'):
            strObjbytes = strObj.encode('utf-8')
            AEScipher = AES.new(self.AESKey, AES.MODE_EAX)
            ciphertext, tag = AEScipher.encrypt_and_digest(strObjbytes)
            packet = {'0':AEScipher.nonce.hex(), '1':tag.hex(), '2':ciphertext.hex()}
            cipherObj = json.dumps(packet)
            return cipherObj.encode('utf-8')
        else:
            blocks = self.segmentPacket(strObj, 256)

            for k, v in blocks.items():
                encodeBlock = self.RSARemotePublicKey.encrypt(v.encode('utf-8'), 
                    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
                blocks[k] = encodeBlock.hex()
            strBlocks = json.dumps(blocks)

            return strBlocks.encode('utf-8')
        
    def decode(self, obj, typeObject):
        strObj = ''
        try:
            if self.Encrypter == 'AES' :
                cipherObj = json.loads(obj.decode('utf-8'))
                nonce = bytes.fromhex(cipherObj['0'])
                tag = bytes.fromhex(cipherObj['1'])
                ciphertext = bytes.fromhex(cipherObj['2'])
                AEScipher = AES.new(self.AESKey, AES.MODE_EAX, nonce)
                strObjbytes = AEScipher.decrypt_and_verify(ciphertext, tag)
                strObj = strObjbytes.decode('utf-8')
            else:
                blocks = json.loads(obj.decode('utf-8'))
                for v in blocks.values():
                    decodeBlock = self.RSALocalPrivateKey.decrypt(bytes.fromhex(v), 
                        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(), label=None))
                    strObj += decodeBlock.decode('utf-8')
        except Exception as e:
            print(obj)
            print(e)
            return None
            
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
