from public_api import create_api
from controller.controller import Controller

def setup(replicas=[]):
    master_controller = Controller(is_master=True, replicas=replicas)
    create_api(getter=master_controller.get_messages, masterCallback=master_controller.add_message).run(port=3000)


if __name__ == "__main__":
    setup()
