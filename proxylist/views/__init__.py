import os

from proxylist.metrics import register_metrics
from proxylist.views.config_file import json_proxy_file
from proxylist.views.country_api import CountryCodeViewSet
from proxylist.views.healthcheck import healthcheck
from proxylist.views.html_proxy_list import list_proxies
from proxylist.views.port_api import PortViewSet
from proxylist.views.proxy_api import ProxyViewSet
from proxylist.views.qr_code import qr_code
from proxylist.views.subscription_api import SubViewSet, Base64SubViewSet

if "gunicorn" in os.environ.get("SERVER_SOFTWARE", ""):
    register_metrics()
