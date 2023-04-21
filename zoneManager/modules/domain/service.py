
from project.config.system import KEY
from project.config.enum import API
from project.util import log
from project.util import get
import requests
import json


def getCloudflareDns(targetDomain=None):
    url = f'{API["CLOUDFLARE"]}'
    headers = {
        "Authorization": KEY["CLOUDEFLARE"],
        "Content-Type": "application/json"
    }
    data = get(url, headers)
    r = requests.get(url, headers=headers)
    # 解析 JSON 响應...
    response_data = json.loads(r.content)
    log(response_data, __name__)

    # 格式化輸出日誌信息...
    # logger.info(json.dumps(response_data, indent=4))

    r.connection.close()

    p = json.loads(r.text)

    return p
