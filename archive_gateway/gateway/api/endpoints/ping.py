from flask_restplus import Resource, Namespace

ns = Namespace('ping', description='Check if the api is up')


@ns.route('/')
class Ping(Resource):
    def get(self):
        return {'message': 'pong'}
