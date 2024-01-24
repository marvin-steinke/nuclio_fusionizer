def handler(context, event, requests_session):
    return int(event.body["value1"]) + int(event.body["value2"])