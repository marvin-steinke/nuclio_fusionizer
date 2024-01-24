def handler(context, event, requests_session):
    return event.body["value1"] + event.body["value2"]