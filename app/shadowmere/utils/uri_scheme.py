import base64

from utils.base64_decoder import decode_base64


def get_sip002(instance_url):
    try:
        url = instance_url
        if "#" in url:
            url = url.split("#")[0]
        if "=" in url:
            url = url.replace("=", "")
        if "@" not in url:
            url = url.replace("ss://", "")
            decoded_url = decode_base64(url.encode("ascii"))
            if decoded_url:
                encoded_bits = base64.b64encode(decoded_url.split(b"@")[0]).decode("ascii").rstrip("=")
                url = f'ss://{encoded_bits}@{decoded_url.split(b"@")[1].decode("ascii")}'
            else:
                return ""
    except IndexError:
        return ""

    return url
