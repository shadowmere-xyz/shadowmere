import base64
import binascii
import re


def decode_base64(data, altchars=b"+/"):
    """Decode base64, padding being optional.
    source: https://stackoverflow.com/questions/2941995/python-ignore-incorrect-padding-error-when-base64-decoding
    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    data = re.sub(rb"[^a-zA-Z0-9%s]+" % altchars, b"", data)  # normalize
    missing_padding = len(data) % 4
    if missing_padding:
        data += b"=" * (4 - missing_padding)
    try:
        return base64.b64decode(data, altchars)
    except binascii.Error:
        return None
