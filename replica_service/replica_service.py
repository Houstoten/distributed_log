import grpc
from concurrent import futures
import time
import threading

import message_send_pb2
import message_send_pb2_grpc

class MessageServicer(message_send_pb2_grpc.ReceiverServicer):
    def __init__(self, callback):
        self.callback = callback

    def NewMessage(self, request, context):
        self.callback(request.msg, request.msg_id)
        response = message_send_pb2.Empty()
        return response

def start_grpc_server(callback_fn):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    message_servicer = MessageServicer(callback_fn)
    message_send_pb2_grpc.add_ReceiverServicer_to_server(message_servicer, server)
    server.add_insecure_port('0.0.0.0:50051')
    server.start()
    print('gRPC server started on port 50051')
    try:
        while True:
            time.sleep(86400)  
    except KeyboardInterrupt:
        server.stop(0)
