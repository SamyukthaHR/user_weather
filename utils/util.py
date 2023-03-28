import json


def format_serializer_data(serializer_data):
    return json.loads(json.dumps(serializer_data))
