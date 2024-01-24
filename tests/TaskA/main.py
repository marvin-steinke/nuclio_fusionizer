import requests
import json

def handler(context, event, requests_session):
    fusionizer_address = event.headers["Fusionizer-Server-Address"]
    # invoke Task B
    url = f"http://{fusionizer_address}:8000/taskb"
    response = requests.get(url)
    return response.text
    headers = {"Content-Type": "application/json"}
    data = {"value1": "5", "value2": "3"}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response