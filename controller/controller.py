import grpc

import message_send_pb2
import message_send_pb2_grpc

import sync_replica_pb2
import sync_replica_pb2_grpc

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

def send_msg_to_replica(msg, id, replica, latch, missing_replicas):
    channel = grpc.insecure_channel(replica)
    stub = message_send_pb2_grpc.ReceiverStub(channel)
    message = message_send_pb2.Msg(msg_id=id, msg=msg)

    try:
        response = stub.NewMessage(message)
        if response:
            print(f"{replica} OK!")    

            if replica in missing_replicas: missing_replicas.remove(replica)
        else:
            print(f"{replica} Error!")
            missing_replicas.add(replica)
    except:
        missing_replicas.add(replica)
    
    if latch is not None: latch.count_down()


def send_missed_on_appear(missing_pair, stub):
    bulk_list_ids, bulk_list_values = missing_pair

    sync_replica_request = sync_replica_pb2.MissedMessages(ids=bulk_list_ids, values=bulk_list_values)
    stub.BatchUpdate(sync_replica_request)

def heartbeat_replicas(replicas, not_available, all_messages):
    for replica in replicas:
        channel = grpc.insecure_channel(replica)
        stub = sync_replica_pb2_grpc.SyncReplicaStub(channel)
        was_missing_msg = sync_replica_pb2.OneBeat(was_missing=True if replica in not_available else False) 

        print(replica, ' ----------------------------')
        try:
            response = stub.HeartBeat(was_missing_msg)
            if response:
                print(f"{replica} Alive!")    
                if replica in not_available: 

                    missing_ids = list(set(range(len(all_messages))) - set(response.known_ids))
                    missing_items = [i for j, i in enumerate(all_messages) if j not in response.known_ids]
                    send_missed_on_appear((missing_ids, missing_items), stub)

                    not_available.remove(replica)
            else:
                print(f"{replica} Missing!")
                not_available.add(replica)
        except:
            print(f"{replica} Missing!")
            not_available.add(replica)
    
    return None

class Controller:
    messages = []
    missing_replicas = set()
    #should be sorted dict
    replica_messages = dict()
    replicas = []
    is_master = False

    def __init__(self, is_master, replicas = []):
        self.is_master = is_master
        self.replicas = replicas
        if is_master:
            self.heartbeat_thread = threading.Thread(target=self.heartbeat)
            self.heartbeat_thread.daemon = True
            self.heartbeat_thread.start()

    def add_master_message(self, msg, write_concern):
        lock.acquire()
        self.messages.append(msg)
        index = len(self.messages) - 1
        lock.release()

        logging.info("Sending message to replicas: " + msg)
        latch = CountDownLatch(len(self.replicas) if write_concern == 0 else min(write_concern - 1, len(self.replicas)))
        replica_threads = []
        for replica in self.replicas:
            rpc_req = threading.Thread(target=lambda: send_msg_to_replica(msg, index, replica, latch, self.missing_replicas))
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

    def update_replica_dict_bulk(self, new_dict):
        self.replica_messages = self.replica_messages | new_dict
    
    def heartbeat(self):
        while True:
            time.sleep(5)
            logging.info("Heartbeat!")
            heartbeat_replicas(self.replicas, self.missing_replicas, self.messages)
