import json


class Protocol:
    @staticmethod
    def create_message(command, data=None):
        return json.dumps({"command": command, "data": data or {}})

    @staticmethod
    def parse_request(message):
        return json.loads(message)

    @staticmethod
    def parse_response(message):
        return json.loads(message)

    @staticmethod
    def create_response(command, data):
        return {"command": command, "data": data}
