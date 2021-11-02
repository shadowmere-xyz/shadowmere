import logging
import os
import signal
import socket
import subprocess
from contextlib import closing
from time import sleep

import requests


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def get_proxy_location(proxy_url):
    port = find_free_port()
    cmd = f'sslocal -v -b localhost:{port} --server-url {proxy_url}'
    pro = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                           shell=True, preexec_fn=os.setsid)
    sleep(0.3)
    try:
        r = requests.get(
            "https://myip.wtf/json",
            proxies={"http": f"socks5://127.0.0.1:{port}", "https": f"socks5://127.0.0.1:{port}"},
            timeout=5,
        )
        output = r.json()
        if r.status_code != 200 or "YourFuckingLocation" not in output:
            return None
        return output.get("YourFuckingLocation")
    except Exception as e:
        logging.error(f"call to myip.wtf/json failed {e}")
        return None
    finally:
        os.killpg(os.getpgid(pro.pid), signal.SIGTERM)


def update_proxy_status(proxy):
    location = get_proxy_location(proxy_url=proxy.url)
    if location:
        proxy.is_active = True
        proxy.location = location
    else:
        proxy.is_active = False
        proxy.location = "unknown"
    proxy.save()
