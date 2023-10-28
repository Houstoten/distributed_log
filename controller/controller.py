import grpc

import message_send_pb2
import message_send_pb2_grpc

import threading
import logging
import time
import random

class CountDownLatch():
    def __init__(self, count):
        self.count = count
        self.condition = threading.Condition()
 
    def count_down(self):
        with self.condition:
            if self.count == 0:
                return
            self.count -= 1
            if self.count == 0:
                self.condition.notify_all()
 
    def wait(self):
        with self.condition:
            if self.count == 0:
                return
            self.condition.wait()

lock = threading.Lock()

def send_msg_to_replica(msg, id, replica, latch):
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
    
    latch.count_down()

class Controller:
    messages = []
    #should be sorted dict
    replica_messages = dict()
    replicas = []
    is_master = False

    def __init__(self, is_master, replicas = []):
        self.is_master = is_master
        self.replicas = replicas

    def add_master_message(self, msg, write_concern):
        lock.acquire()
        self.messages.append(msg)
        index = len(self.messages) - 1
        lock.release()

        logging.info("Sending message to replicas: " + msg)
        latch = CountDownLatch(len(self.replicas) if write_concern == 0 else min(write_concern - 1, len(self.replicas)))
        replica_threads = []
        for replica in self.replicas:
            rpc_req = threading.Thread(target=lambda: send_msg_to_replica(msg, index, replica, latch))
            replica_threads.append(rpc_req)
            rpc_req.start()
        
        logging.info(f"Message sent to {len(replica_threads)} replicas.")
        latch.wait()
        
        logging.info("Message successfully replicated")
        return
    
    def add_message_replica(self, msg, index):

        logging.info("Adding new value from master: " + msg)
        logging.info("Waiting 3 seconds...")
        time.sleep(3)
        lock.acquire()
        if index not in self.replica_messages:
           self.replica_messages[index] = msg
        lock.release()

        logging.info("Added new value from master: " + msg)
        logging.info("Releasing")
        return

    def get_messages(self):
        if self.is_master:
            return self.messages
        else:
            msgs_replica = []
            for (k, v) in sorted(self.replica_messages.items(), key=lambda x: x[0]):
                if k == len(msgs_replica):
                    msgs_replica.append(v)
                else:
                    break
            return msgs_replica
