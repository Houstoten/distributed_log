import grpc

# import the generated classes
import message_send_pb2
import message_send_pb2_grpc

import threading

lock = threading.Lock()

class Controller:
    messages = []
    replicas = []
    is_master = False

    def __init__(self, is_master, replicas = []):
        self.is_master = is_master
        self.replicas = replicas

    def add_message(self, msg):

        lock.acquire()
        self.messages.append(msg)
        index = len(self.messages) - 1
        lock.release()

        if self.is_master:
            for replica in self.replicas:
                channel = grpc.insecure_channel(replica)
                stub = message_send_pb2_grpc.ReceiverStub(channel)
                message = message_send_pb2.Msg(msg_id=index, msg=msg)

                try:
                    response = stub.NewMessage(message)
                    if response:
                        print("OK!")
                    else:
                        print("Error!")
                except:
                    print("Error!")
            # print('forward ', msg, ' to ', len(self.replicas), ' replicas')
        return
    
    def get_messages(self):
        return self.messages
        
