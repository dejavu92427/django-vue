import json
import sys
import socket
import requests
import datetime
from OpenSSL import SSL, crypto
import pymongo

import multiprocessing.pool
import functools

def timeout(max_timeout):
    """Timeout decorator, parameter in seconds."""
    def timeout_decorator(item):
        """Wrap the original function."""
        @functools.wraps(item)
        def func_wrapper(*args, **kwargs):
            """Closure for function."""
            pool = multiprocessing.pool.ThreadPool(processes=1)
            async_result = pool.apply_async(item, args, kwargs)
            # raises a TimeoutError if execution exceeds max_timeout
            return async_result.get(max_timeout)
        return func_wrapper
    return timeout_decorator


myclient = pymongo.MongoClient("mongodb://172.18.0.2:27017/")

mydb = myclient["mydb"]

mycol = mydb["myc"]

def sendAlert(msg):
    url = "https://cqgame.info/API/IMService.ashx"

    headers = {
        "Content-type": "application/x-www-form-urlencoded",
    }

    data = {
        "ask": "sendChatMessage",
        "account": "sysbot",
        "api_key": "DF48F6B5-5CEB-0AA2-A7FC-939FBDA0AB08",
        "chat_sn": "2615",
        "content_type": "1",
        "msg_content": msg
    }

    requests.post(url, data=data, headers=headers)


def make_context():
    context = SSL.Context(method=SSL.TLSv1_2_METHOD)
    #for bundle in [requests.certs.where(), '/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem']:
    #    context.load_verify_locations(cafile=bundle)
    return context


@timeout(8)
def print_chain(context, hostname):
    print('Getting certificate chain for {0}'.format(hostname))
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = SSL.Connection(context=context, socket=sock)
        sock.settimeout(5)
        sock.set_tlsext_host_name(hostname.encode())
        try:
            sock.connect((hostname, 443))
        except:
            raise BaseException("Error")

        sock.setblocking(1)
        sock.do_handshake()
        notafter = sock.get_peer_certificate().get_notAfter().decode('ascii')
        utcafter = datetime.datetime.strptime(notafter, "%Y%m%d%H%M%SZ")
        utcnow = datetime.datetime.utcnow()
        alertTime = datetime.timedelta(days=7)
        expired = datetime.timedelta(days=0)
        timeToExpired = utcafter - utcnow

        if timeToExpired < expired:
            msg = f"{hostname} SSL certificate expired {-timeToExpired}"
            print(msg)
            sendAlert(msg)
        elif timeToExpired < alertTime:
            msg = f"{hostname} SSL certificate will expire after {timeToExpired}"
            print(msg)
            sendAlert(msg)
        elif timeToExpired < alertTime:
            msg = f"{hostname} SSL certificate will expire after {timeToExpired}"
            print(msg)
            sendAlert(msg)
        else:
            print(' 0 e: {0} [{1}]'.format(timeToExpired, notafter))

        oldI = ""
        for (idx, cert) in enumerate(sock.get_peer_cert_chain()):
            s = cert.get_subject()
            if oldI != s and idx > 0:
                msg = f"{hostname} SSL certificate chain error"
                print(msg)
                sendAlert(msg)
            oldI = cert.get_issuer()
            print(' {0} s:{1}'.format(idx, cert.get_subject()))
            print(' {0} i:{1}'.format(' ', cert.get_issuer()))
    except:
        pass
    finally:
        sock.shutdown()
        sock.close()


if __name__ == "__main__":
    context = make_context()
    #for hostname in sys.stdin:

    now = datetime.datetime.now()

    check = now - datetime.timedelta(days=1)

    domainList = mycol.find({"updateTime": {"$gte": check}}).distinct('domain')

    for hostname in domainList:
        if hostname:
            hostname = hostname.strip('.').strip()
            try:
                hostname.index('.')
                print_chain(context, hostname)
            except Exception as e:
                print('   f:{0}'.format(e))
                try:
                    hostname = 'www.'+hostname
                    print_chain(context, hostname)
                except:
                    print('   f:{0}'.format(e))

