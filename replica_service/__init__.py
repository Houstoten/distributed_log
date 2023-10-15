import grpc
from concurrent import futures
import time
import threading

# Import your generated gRPC service and implementation
# Replace `your_generated_module` and `YourServiceServicer` with the appropriate values.
import message_send_pb2
import message_send_pb2_grpc

# def someprint(i, msg):
#     print(i, msg)

class MessageServicer(message_send_pb2_grpc.ReceiverServicer):
    def __init__(self, callback):
        self.callback = callback

    def NewMessage(self, request, context):
        # print(request.msg, request.msg_id)
        # self.callback(request.msg_id, request.msg)
        self.callback(request.msg)
        response = message_send_pb2.Empty()
        return response
        # return
        # return super().NewMessage(request, context)

# Define the gRPC server function
def start_grpc_server(callback_fn):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    message_servicer = MessageServicer(callback_fn)
    message_send_pb2_grpc.add_ReceiverServicer_to_server(message_servicer, server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print('gRPC server started on port 50051')
    try:
        while True:
            time.sleep(86400)  # Keep the server running
    except KeyboardInterrupt:
        server.stop(0)


# Create a separate thread to start the gRPC server
# server_thread = threading.Thread(target=start_grpc_server)
# server_thread.start()