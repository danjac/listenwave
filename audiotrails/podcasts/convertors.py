from __future__ import annotations

import functools

from typing import Any, Callable, Iterable, Union

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.encoding import force_str

from audiotrails.podcasts.date_parser import parse_date

Validator = Union[Callable, list[Callable]]


def conv(
    *values: Iterable[Any],
    convert: Callable,
    validator: Validator | None = None,
    default: Any = None,
) -> Any:
    """Returns first non-falsy value, converting the item. Otherwise returns default value"""
    for value in values:
        if value and (converted := _conv(value, convert, validator)):
            return converted
    return default() if callable(default) else default


def _conv(value: Any, convert: Callable, validator: Validator | None = None) -> Any:
    try:
        return _validate(convert(value), validator)
    except (ValidationError, TypeError, ValueError):
        return None


def _validate(value: Any, validator: Validator | None) -> Any:
    if None in (value, validator):
        return value

    validators = [validator] if callable(validator) else validator

    for _validator in validators:
        _validator(value)

    return value


conv_str = functools.partial(conv, convert=force_str, default="")
conv_bool = functools.partial(conv, convert=bool, default=False)
conv_list = functools.partial(conv, convert=list, default=list)
conv_int = functools.partial(conv, convert=int)
conv_date = functools.partial(conv, convert=parse_date)

conv_url = functools.partial(
    conv,
    convert=force_str,
    default="",
    validator=URLValidator(schemes=["http", "https"]),
)
