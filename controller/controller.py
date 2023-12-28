import grpc

import message_send_pb2
import message_send_pb2_grpc

import sync_replica_pb2
import sync_replica_pb2_grpc

import threading
import logging
import time
import random
import enum

class ReplicaStatus(enum.Enum):
    healthy = 'healthy'
    suspected = 'suspected'
    unhealthy = 'unhealthy'

suspected_to_unhealthy_rate = 3

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

def retry_with_backoff(retries = 3, backoff_in_seconds = 1):
    def rwb(f):
        def wrapper(*args, **kwargs):
          x = 0
          while True:
            try:
              return f(*args, **kwargs)
            except:
              if x == retries:
                raise

              sleep = (backoff_in_seconds * 2 ** x +
                       random.uniform(0, 1))
              time.sleep(sleep)
              x += 1
                
        return wrapper
    return rwb

def send_msg_to_replica(msg, id, replica, latch):
    channel = grpc.insecure_channel(replica)
    stub = message_send_pb2_grpc.ReceiverStub(channel)
    message = message_send_pb2.Msg(msg_id=id, msg=msg)

    try:
        response = stub.NewMessage(message)
        if response:
            logging.info(f"{replica} OK!")    

        else:
            # logging.info(f"{replica} Error!")
            raise
    except:
        logging.info(f"{replica} Error!")
        raise
    
    if latch is not None: latch.count_down()

def send_msg_to_replica_with_retry(msg, id, replica, latch, suspected_replicas, missing_replicas):
    try:
        # retry count
        # 0 for clearly missing
        # 3 for suspected
        # 5 for healthy
        retry_with_backoff(retries = 0 if replica in missing_replicas else 3 if replica in suspected_replicas else 5)(send_msg_to_replica)(msg, id, replica, latch)
        if replica in suspected_replicas: del suspected_replicas[replica]
        if replica in missing_replicas: missing_replicas.remove(replica)
    except:
        missing_replicas.add(replica)

def send_missed_on_appear(missing_pair, stub):
    bulk_list_ids, bulk_list_values = missing_pair

    sync_replica_request = sync_replica_pb2.MissedMessages(ids=bulk_list_ids, values=bulk_list_values)
    stub.BatchUpdate(sync_replica_request)

def suspected_check(replica, suspected, not_available):
    if replica in suspected:
        if suspected[replica] >= suspected_to_unhealthy_rate - 1:
            del suspected[replica]
            not_available.add(replica)
        else:
            suspected[replica] += 1
    elif replica not in not_available:
        suspected[replica] = 0

def heartbeat_replicas(replicas, not_available, suspected, all_messages):
    for replica in replicas:
        channel = grpc.insecure_channel(replica)
        stub = sync_replica_pb2_grpc.SyncReplicaStub(channel)
        was_missing_msg = sync_replica_pb2.OneBeat(was_missing=True if replica in not_available else False) 

        try:
            response = stub.HeartBeat(was_missing_msg)
            if response:
                logging.info(f"{replica} Alive!")    
                if replica in not_available or replica in suspected: 

                    missing_ids = list(set(range(len(all_messages))) - set(response.known_ids))
                    missing_items = [i for j, i in enumerate(all_messages) if j not in response.known_ids]
                    send_missed_on_appear((missing_ids, missing_items), stub)

                    if replica in not_available: not_available.remove(replica)
                    if replica in suspected: del suspected[replica]
            else:
                # logging.info(f"{replica} Missing!")
                # suspected_check(replica, suspected, not_available)
                raise
                
        except:
            logging.info(f"{replica} Missing!")
            suspected_check(replica, suspected, not_available)
    
    return None

class Controller:
    messages = []
    missing_replicas = set()
    suspected_replicas = dict()
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
            rpc_req = threading.Thread(target=lambda: send_msg_to_replica_with_retry(msg, index, replica, latch, self.suspected_replicas, self.missing_replicas))
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
            heartbeat_replicas(self.replicas, self.missing_replicas, self.suspected_replicas, self.messages)
    
    def health_check(self):
        return list(map(lambda replica: {replica: 'unhealthy' if replica in self.missing_replicas else 'suspected' if replica in self.suspected_replicas else 'healthy'}, self.replicas))
