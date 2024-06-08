from django.core.exceptions import ValidationError
from utils.proxy import get_proxy_location
from utils.uri_scheme import get_sip002


def validate_sip002(value: str) -> None:
    if get_sip002(value) == "":
        raise ValidationError(
            "The value entered is not SIP002 compatible",
            params={"value": value},
        )


def validate_proxy_can_connect(value: str) -> None:
    location = get_proxy_location(get_sip002(value))
    if location is None or location == "unknown":
        raise ValidationError(
            "Can't get the location for this address",
            params={"value": value},
        )


def proxy_validator(value: str) -> None:
    validate_sip002(value)
    validate_proxy_can_connect(value)
