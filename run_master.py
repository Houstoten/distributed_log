from public_api import create_api
from controller.controller import Controller

# import grpc

# import the generated classes
# import message_send_pb2
# import message_send_pb2_grpc


if __name__ == "__main__":
    master_controller = Controller(is_master=True, replicas=['localhost:50051'])
    # def getter(self): 
    #     return [1, 2, 3, 4]

    create_api(getter=master_controller.get_messages, masterCallback=master_controller.add_message).run(port=3000)

    # channel = grpc.insecure_channel('localhost:50051')
    # stub = message_send_pb2_grpc.ReceiverStub(channel)
    # message = message_send_pb2.Msg(msg_id=3, msg='aabb')

    # try:
    #     response = stub.NewMessage(message)
    #     if response:
    #         print("OK!")
    #     else:
    #         print("Error!")
    # except:
    #     print("Error!")

