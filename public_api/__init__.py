from flask import Flask, request, abort
from flask_restful import Resource, Api

class MessageController(Resource):
    def post(self):
        if not hasattr(self, 'masterCallback'):
            abort(404)

        self.masterCallback(request.get_data(as_text=True))
        pass

    def get(self):
        return self.getter()

    @classmethod
    def set_master_callback(cls, callback):
        cls.masterCallback = callback
        return cls
    
    @classmethod
    def set_getter(cls, getter):
        cls.getter = getter
        return cls

def create_api(getter, masterCallback=None):
    app = Flask(__name__)
    api = Api(app)
    DomainMessageController = MessageController

    if masterCallback is not None:
        DomainMessageController = DomainMessageController.set_master_callback(masterCallback)

    DomainMessageController = DomainMessageController.set_getter(getter)
    api.add_resource(DomainMessageController, '/')

    return app
