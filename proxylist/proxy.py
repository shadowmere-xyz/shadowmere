import json

import docker
from docker.errors import ContainerError


def get_proxy_location(proxy_url):
    client = docker.from_env()
    try:
        output = client.containers.run(image="guamulo/testssproxy", command=proxy_url,
                                       remove=True,
                                       detach=False,
                                       stdout=True, )
    except ContainerError:
        return None

    if "YourFuckingIPAddress" in str(output):
        return json.loads(output).get("YourFuckingLocation")

    return None


def update_proxy_status(proxy):
    location = get_proxy_location(proxy_url=proxy.url)
    if location:
        proxy.is_active = True
        proxy.location = location
    else:
        proxy.is_active = False
        proxy.location = "unknown"
    proxy.save()
