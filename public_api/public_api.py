from flask import Flask, request, abort
from flask_restful import Resource, Api

class MessageController(Resource):
    def post(self):
        if not hasattr(self, 'masterCallback'):
            abort(404)

        self.masterCallback(request.get_data(as_text=True), request.args.get('write_concern', 0, type=int))
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
        
class HealthController(Resource):
    def get(self):
        return self.health_check()
    
    @classmethod
    def set_health_check(cls, callback):
        cls.health_check = callback
        return cls

def create_api(getter, masterCallback=None, health_check=None):
    app = Flask(__name__)
    api = Api(app)
    DomainMessageController = MessageController

    if health_check is not None:
        DomainHealthController = HealthController
        DomainHealthController = DomainHealthController.set_health_check(health_check)
        api.add_resource(DomainHealthController, '/health')

    if masterCallback is not None:
        DomainMessageController = DomainMessageController.set_master_callback(masterCallback)

    DomainMessageController = DomainMessageController.set_getter(getter)
    api.add_resource(DomainMessageController, '/')

    return app
