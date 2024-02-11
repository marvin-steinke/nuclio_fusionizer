def handler(context, event, requests_session):
    target = int(event.body["value"])
    actual = 0

    fusionizer_address = event.headers["Fusionizer-Server-Address"]
    # invoke addition task
    url = f"http://{fusionizer_address}:8000/additiontask"
    headers = {"Content-Type": "application/json"}
    data = {"value": event.body["value"]}
    
    while actual < target:
        response = requests_session.post(url, headers=headers, json=data)
        actual = int(response.text)

    return actual