from public_api.public_api import create_api
from controller.controller import Controller
from replica_service.replica_service import start_grpc_server
import threading

def setup():
    replica_controller = Controller(is_master=False)

    def start_grpc_server_with_callback():
        start_grpc_server(replica_controller.add_message_replica)

    server_thread = threading.Thread(target=start_grpc_server_with_callback)
    server_thread.start()

    create_api(getter=replica_controller.get_messages).run(port=3000, host="0.0.0.0")

if __name__ == "__main__":
    setup()
