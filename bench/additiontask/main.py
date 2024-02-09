def handler(context, event, requests_session):
    return int(event.body["value"]) + 1