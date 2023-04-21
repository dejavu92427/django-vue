import requests
import json
import gc
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

huaweiB2CName = config['huaweiB2C']['name']
huaweiB2CPass = config['huaweiB2C']['pass']

huaweiB2BName = config['huaweiB2B']['name']
huaweiB2BPass = config['huaweiB2B']['pass']

headers = {
    "Content-type": "application/json;charset=utf8",
}

###################################################################################################

#Huawei B2C API token refresh
data = {
    "auth": {
        "identity": {
            "methods": ["password"],
            "password": {
                "user": {
                    "name": huaweiB2CName,
                    "password": huaweiB2CPass,
                    "domain": {
                        "name": huaweiB2CName
                    }
                }
            }
        },
        "scope": {
            "project": {
                "name": "cn-north-1"
            }
        }
    }
}

url = "https://iam.myhuaweicloud.com/v3/auth/tokens"

r = requests.post(url, headers=headers, json=data)

r.connection.close()

parsed = json.loads(r.text)

with open('/opt/prom/dragonball/utility/huaweiTokenB2C.yml', 'w') as f:
    f.write(r.headers['X-Subject-Token'])

###################################################################################################

#Huawei B2B API token refresh
data = {
    "auth": {
        "identity": {
            "methods": ["password"],
            "password": {
                "user": {
                    "name": huaweiB2BName,
                    "password": huaweiB2BPass,
                    "domain": {
                        "name": huaweiB2BName
                    }
                }
            }
        },
        "scope": {
            "project": {
                "name": "cn-north-1"
            }
        }
    }
}

url = "https://iam.myhuaweicloud.com/v3/auth/tokens"

r = requests.post(url, headers=headers, json=data)

r.connection.close()

parsed = json.loads(r.text)

with open('/opt/prom/dragonball/utility/huaweiTokenB2B.yml', 'w') as f:
    f.write(r.headers['X-Subject-Token'])


gc.collect()
