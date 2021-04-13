from VotingProtocol.Entities import *
import VotingProtocol.Communication.Communication as Comm
import time
import json
from threading import Thread

def VotingClient():
    # Discover servers infos
    SIGNATURE_PUBLIC_BYTES = b'-----BEGIN PUBLIC KEY-----\nMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAw5Hpiz94ZP0XTwU9iDuM\nlQG6MZtKG99OXV/T56XX5WihucaIYSkZB/yMVX9wC898LS9szYxrKmCbOrp9R9Oc\n1L3Z0ySk8QTjuA4uybcbV2+a6hUY6QPOFOtnadfQvPN3B93J9vyjNUAPpEJ9l6tF\n5x0/7o3OdGaRkk/AecmyaY8kFqr5wynrIEDBsg7CNSdHafozq38uuU+0EjeuGkjZ\n3TWI/kolbggFsIPiF5Reuctd2javS/ndIz/kcUsuuwoQh2RECsmIYkYARcKeaeOa\nGAECURF617OCLH9BuXDXr7xOy90hpSE+uyxxxLHu2tdo4WiqdN9OYuk6a6ao5EV/\ncWxTPPzAGkC91sprRQfd0+AcC/F1lqsl2PGTenWkePTA3w6RvH2QLeY3JBXSNisV\nn7ZSCeCAdX3XVkFcr2AuphGg/xwcVi3tZQUfLGEFLg4JQAhSZQaxwAdNVtn7wrCg\nyu+1wkdlGqHAB6V89AK9pVEXjEtdSnTpqQV7NkkAZrlDiS5IeMTRX53Zxay9USAs\nt9YbcGXK+Tc/Dmzm98V8c6hzL86sK1ljMEak0FUfSgWhICeDKTT7tS2T+mAYRePo\ngoVaJzcccCdqP4P7uudwk7E/kN6yDgSdFmjc1/HRcIQjh5iz2IPnC+yOvp8NuJyQ\n6E1Nj+U80gHC3C0PjJ3DGq0CAwEAAQ==\n-----END PUBLIC KEY-----\n'
    CommUDPSocket = Comm.startUDPSocket('CLIENT')
    hello = Comm.UDPDiscoverValidsServers(CommUDPSocket, SIGNATURE_PUBLIC_BYTES)

    if hello is not None:
        print(hello)
        Comm.setupRemoteServer(hello.ServerAddress, hello.PublicKey)

    CommUDPSocket.close()

    # Conect in server
    Comm.TCPClientRunner()

    