from public_api import create_api
from controller.controller import Controller
from replica_service import start_grpc_server
# import replica_service
import threading

if __name__ == "__main__":
    replica_controller = Controller(is_master=False)
    # def getter(self): 
    #     return [1, 2, 3, 4]

    def start_grpc_server_with_callback():
        start_grpc_server(replica_controller.add_message)

    server_thread = threading.Thread(target=start_grpc_server_with_callback)
    server_thread.start()

    create_api(getter=replica_controller.get_messages).run(port=3001)

    # server_thread = threading.Thread(target=start_grpc_server)
    # server_thread.start()
# import replica_service

# if __name__ == "__main__":
#     replica_service.start_grpc_server()
