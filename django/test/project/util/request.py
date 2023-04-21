import requests
import json


def get(url, headers):

    res = requests.get(url, headers=headers)
    # 解析 JSON 响應...
    return json.loads(res.content)
