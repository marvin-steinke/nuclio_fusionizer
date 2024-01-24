def handler(context, event, requests_session):
    fusionizer_address = event.headers["Fusionizer-Server-Address"]
    # invoke Task B
    url = f"http://{fusionizer_address}:8000/taskb"
    headers = {"Content-Type": "application/json"}
    data = {"value1": 5, "value2": 3}
    response = requests_session.post(url, headers=headers, json=data)
    return response.text