import grpc
from concurrent import futures
import time
import threading

import message_send_pb2
import message_send_pb2_grpc

import sync_replica_pb2
import sync_replica_pb2_grpc

class MessageServicer(message_send_pb2_grpc.ReceiverServicer):
    def __init__(self, callback):
        self.callback = callback

    def NewMessage(self, request, context):
        self.callback(request.msg, request.msg_id)
        response = message_send_pb2.Empty()
        return response

class SyncServicer(sync_replica_pb2_grpc.SyncReplicaServicer):
    def __init__(self, getKnownCallback, batchUpdateCallback):
        self.getKnownCallback = getKnownCallback
        self.batchUpdateCallback = batchUpdateCallback

    def HeartBeat(self, request, context):
        if request.was_missing:
            response = sync_replica_pb2.KnownMessages()
            response.known_ids.extend(self.getKnownCallback())
            # response.known_ids.extend([1, 2])
            return response
        
        response = sync_replica_pb2.KnownMessages()
        response.known_ids.extend([])
        return response
    
    def BatchUpdate(self, request, context):
        print(request)
        result_dict = {request.ids[i]: request.values[i] for i in range(len(request.ids))}
        print(result_dict)
        self.batchUpdateCallback(result_dict)

        response = sync_replica_pb2.BoolEmpty()
        return response


def start_grpc_server(msg_callback_fn, get_known_callback, batch_update_callback):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    message_servicer = MessageServicer(msg_callback_fn)
    message_send_pb2_grpc.add_ReceiverServicer_to_server(message_servicer, server)

    sync_servicer = SyncServicer(get_known_callback, batch_update_callback)
    sync_replica_pb2_grpc.add_SyncReplicaServicer_to_server(sync_servicer, server)

    server.add_insecure_port('0.0.0.0:50051')
    server.start()
    print('gRPC server started on port 50051')
    try:
        while True:
            time.sleep(86400)  
    except KeyboardInterrupt:
        server.stop(0)
