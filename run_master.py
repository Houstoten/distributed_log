from public_api.public_api import create_api
from controller.controller import Controller

def setup(replicas=[]):
    master_controller = Controller(is_master=True, replicas=replicas)
    create_api(getter=master_controller.get_messages, masterCallback=master_controller.add_master_message, health_check=master_controller.health_check).run(port=3000, host="0.0.0.0")


if __name__ == "__main__":
    setup()

