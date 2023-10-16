import grpc

import message_send_pb2
import message_send_pb2_grpc

import threading
import logging
import time

lock = threading.Lock()

def send_msg_to_replica(msg, id, replica):
    channel = grpc.insecure_channel(replica)
    stub = message_send_pb2_grpc.ReceiverStub(channel)
    message = message_send_pb2.Msg(msg_id=id, msg=msg)

    try:
        response = stub.NewMessage(message)
        if response:
            print(f"{replica} OK!")
        else:
            print(f"{replica} Error!")
    except:
        print(f"{replica} Error!")

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

            logging.info("Sending message to replicas: " + msg)

            replica_threads = []
            for replica in self.replicas:
                rpc_req = threading.Thread(target=lambda: send_msg_to_replica(msg, index, replica))
                replica_threads.append(rpc_req)
                rpc_req.start()
            
            logging.info(f"Message sent to {len(replica_threads)} replicas.")
            
            for rpc_thr in replica_threads:
                rpc_thr.join()
            
            logging.info("Message successfully replicated")

        else:
            logging.info("Added new value from master: " + msg)
            logging.info("Waiting 3 seconds...")
            time.sleep(3)
            logging.info("Releasing")
        return
    
    def get_messages(self):
        return self.messages
        
