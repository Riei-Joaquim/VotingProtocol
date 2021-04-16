from VotingProtocol.Entities import *
import json
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
    """
    Responsavel por criar as chaves de criptografia locais e por gerenciar as chaves remotas, sendo responsavel pelo encode e decode de pacotes.
     Por padrão no estado inicial utilizamos o AES como encryter   
    """
    def __init__(self, initialEncryption = 'AES', previousRSAKeys = None):
        self.AESKey =  b'7\rY\x08\x7f\xf9\xdcn\x9a\x18\xd9\xf1:\x8c\x1b\x8a\x93\xf9\xedLC`As\xc2\x9c2\x1f\xa6\x93\xac\xf5'
        self.Encrypter = initialEncryption

        # RSA encryption
        if previousRSAKeys is not None:
            self.RSALocalPrivateKey = previousRSAKeys
            self.RSALocalPublicKey = self.RSALocalPrivateKey.public_key()
        else:
            self.RSALocalPrivateKey = rsa.generate_private_key(public_exponent=65537, key_size=4096)
            self.RSALocalPublicKey = self.RSALocalPrivateKey.public_key()
        
        self.RSARemotePublicKey = None
        self.SignKey = None

    def generateRSAKeyToSigners(self):
        """
        Metodo de setup usado para gerar a chave de assinaturas que certificam a autoridade do server para o cliente, 
         A chave publica sera passada para a funcao principal do cliente e a privada para a funcao principal do servidor.
        """
        RSAPrivateKey = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        RSAPublicKey = RSAPrivateKey.public_key()

        privateBytes = RSAPrivateKey.private_bytes(encoding=serialization.Encoding.PEM, 
                            format=serialization.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=serialization.NoEncryption())
        publicBytes = RSAPublicKey.public_bytes(encoding=serialization.Encoding.PEM,format=serialization.PublicFormat.SubjectPublicKeyInfo)
        print('\n##################### Private Bytes ######################\n')
        print(privateBytes)
        print('\n##################### Public Bytes #######################\n')
        print(publicBytes)

        return privateBytes, publicBytes

    def getLocalPublicKey(self):
        return self.RSALocalPublicKey.public_bytes(encoding=serialization.Encoding.PEM, 
                    format=serialization.PublicFormat.SubjectPublicKeyInfo).decode('utf-8')
    
    def getRemotePublicKey(self):
        if self.RSARemotePublicKey is None:
            return None

        return self.RSARemotePublicKey.public_bytes(encoding=serialization.Encoding.PEM, 
                    format=serialization.PublicFormat.SubjectPublicKeyInfo).decode('utf-8')

    def setRemotePublicKey(self, remotePublicKey):
        """
        Setup para definir a public key do outro comunicante, requisito para podermos trocar o encrytor pelo RSA 
        """
        key = serialization.load_pem_public_key(remotePublicKey.encode())
        if isinstance(key, rsa.RSAPublicKey):
            self.RSARemotePublicKey = key
            self.Encrypter = 'RSA'
        else:
            print('Invalid Public Key!')
    
    def setSignatureKey(self, signature, operation):
        if operation == 'SIGNER':
            self.SignKey = serialization.load_pem_private_key(signature, password=None)
        elif operation == 'VERIFY':
            self.SignKey = serialization.load_pem_public_key(signature)
    
    
    def segmentPacket(self, strObj, blockSize):
        """
        Fragmenta a string em uma lista com N blocos com a quantidade de bytes indicado 
        """
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
    
    def signPacket(self, packetBytes):
        """
        Assina um pacote de bytes recebidos com a chave RSA previamente setada, para garantir autenticidade do conteudo.
         Retornando um pacote em bytes com a assinatura do conteudo.
        """
        hasher = hashes.Hash(hashes.SHA256())
        hasher.update(packetBytes)
        digest = hasher.finalize()
        signature = self.SignKey.sign(
            digest,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=padding.PSS.MAX_LENGTH),
            utils.Prehashed(hashes.SHA256()))
        packet = {'payload': packetBytes.hex(), 'sign':signature.hex()}
        cipherObj = json.dumps(packet)

        return cipherObj.encode('utf-8')
    
    def verifySignPacket(self, packetBytes):
        """
        Verifica a assinatura de um pacote de bytes recebidos com a chave RSA previamente setada, para garantir autenticidade do conteudo.
         Retornando o payload do pacote caso seja confirmado autenticado.
        """
        cipherObj = json.loads(packetBytes.decode('utf-8'))
        payload = bytes.fromhex(cipherObj['payload'])
        sign = bytes.fromhex(cipherObj['sign'])

        try:
            hasher = hashes.Hash(hashes.SHA256())
            hasher.update(payload)
            digest = hasher.finalize()
            self.SignKey.verify(
                sign,
                digest,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                utils.Prehashed(hashes.SHA256()))
        except InvalidSignature as e:
            print(e)
            return None

        return payload

    def encode(self, obj):
        """
        Recebe um objeto DataClass, Converte ele para String e criptografa usando o encrypter definido
         Retornando um objeto bytes, pronto para ser transmitido. 
        """
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
        """
        Recebe um objeto em bytes e tenta converter ele para string e descriptografar usando o encrypter definido.
         o argumento typeObject define como sera passado o retorno, caso seja None, será retornado um objeto dicionario
         com os campos e valores disponiveis, caso seja alguma entidade DataClass o resultado do descriptografia tentara ser
         formatado em um objeto dessa DataClass, em todos os casos voltando None em caso de erro.
        """
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
