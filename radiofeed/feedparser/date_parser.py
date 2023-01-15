from __future__ import annotations

import functools

from datetime import date, datetime
from typing import Final

from dateutil import parser as date_parser
from django.utils.timezone import is_aware, make_aware

_TZ_INFOS: Final = {
    k: v * 3600
    for k, v in (
        ("A", 1),
        ("ACDT", 11),
        ("ACST", 10),
        ("ACT", -5),
        ("ACWST", 9),
        ("ADT", 4),
        ("AEDT", 11),
        ("AEST", 10),
        ("AET", 10),
        ("AFT", 5),
        ("AKDT", -8),
        ("AKST", -9),
        ("ALMT", 6),
        ("AMST", -3),
        ("AMT", -4),
        ("ANAST", 12),
        ("ANAT", 12),
        ("AQTT", 5),
        ("ART", -3),
        ("AST", 3),
        ("AT", -4),
        ("AWDT", 9),
        ("AWST", 8),
        ("AZOST", 0),
        ("AZOT", -1),
        ("AZST", 5),
        ("AZT", 4),
        ("AoE", -12),
        ("B", 2),
        ("BNT", 8),
        ("BOT", -4),
        ("BRST", -2),
        ("BRT", -3),
        ("BST", 6),
        ("BTT", 6),
        ("C", 3),
        ("CAST", 8),
        ("CAT", 2),
        ("CCT", 7),
        ("CDT", -5),
        ("CEST", 2),
        ("CET", 1),
        ("CHADT", 14),
        ("CHAST", 13),
        ("CHOST", 9),
        ("CHOT", 8),
        ("CHUT", 10),
        ("CIDST", -4),
        ("CIST", -5),
        ("CKT", -10),
        ("CLST", -3),
        ("CLT", -4),
        ("COT", -5),
        ("CST", -6),
        ("CT", -6),
        ("CVT", -1),
        ("CXT", 7),
        ("ChST", 10),
        ("D", 4),
        ("DAVT", 7),
        ("DDUT", 10),
        ("E", 5),
        ("EASST", -5),
        ("EAST", -6),
        ("EAT", 3),
        ("ECT", -5),
        ("EDT", -4),
        ("EEST", 3),
        ("EET", 2),
        ("EGST", 0),
        ("EGT", -1),
        ("EST", -5),
        ("ET", -5),
        ("F", 6),
        ("FET", 3),
        ("FJST", 13),
        ("FJT", 12),
        ("FKST", -3),
        ("FKT", -4),
        ("FNT", -2),
        ("G", 7),
        ("GALT", -6),
        ("GAMT", -9),
        ("GET", 4),
        ("GFT", -3),
        ("GILT", 12),
        ("GMT", 0),
        ("GST", 4),
        ("GYT", -4),
        ("H", 8),
        ("HDT", -9),
        ("HKT", 8),
        ("HOVST", 8),
        ("HOVT", 7),
        ("HST", -10),
        ("I", 9),
        ("ICT", 7),
        ("IDT", 3),
        ("IOT", 6),
        ("IRDT", 5),
        ("IRKST", 9),
        ("IRKT", 8),
        ("IRST", 4),
        ("IST", 6),
        ("JST", 9),
        ("K", 10),
        ("KGT", 6),
        ("KOST", 11),
        ("KRAST", 8),
        ("KRAT", 7),
        ("KST", 9),
        ("KUYT", 4),
        ("L", 11),
        ("LHDT", 11),
        ("LHST", 11),
        ("LINT", 14),
        ("M", 12),
        ("MAGST", 12),
        ("MAGT", 11),
        ("MART", 10),
        ("MAWT", 5),
        ("MDT", -6),
        ("MHT", 12),
        ("MMT", 7),
        ("MSD", 4),
        ("MSK", 3),
        ("MST", -7),
        ("MT", -7),
        ("MUT", 4),
        ("MVT", 5),
        ("MYT", 8),
        ("N", -1),
        ("NCT", 11),
        ("NDT", 3),
        ("NFT", 11),
        ("NOVST", 7),
        ("NOVT", 7),
        ("NPT", 6),
        ("NRT", 12),
        ("NST", 4),
        ("NUT", -11),
        ("NZDT", 13),
        ("NZST", 12),
        ("O", -2),
        ("OMSST", 7),
        ("OMST", 6),
        ("ORAT", 5),
        ("P", -3),
        ("PDT", -7),
        ("PET", -5),
        ("PETST", 12),
        ("PETT", 12),
        ("PGT", 10),
        ("PHOT", 13),
        ("PHT", 8),
        ("PKT", 5),
        ("PMDT", -2),
        ("PMST", -3),
        ("PONT", 11),
        ("PST", -8),
        ("PT", -8),
        ("PWT", 9),
        ("PYST", -3),
        ("PYT", -4),
        ("Q", -4),
        ("QYZT", 6),
        ("R", -5),
        ("RET", 4),
        ("ROTT", -3),
        ("S", -6),
        ("SAKT", 11),
        ("SAMT", 4),
        ("SAST", 2),
        ("SBT", 11),
        ("SCT", 4),
        ("SGT", 8),
        ("SRET", 11),
        ("SRT", -3),
        ("SST", -11),
        ("SYOT", 3),
        ("T", -7),
        ("TAHT", -10),
        ("TFT", 5),
        ("TJT", 5),
        ("TKT", 13),
        ("TLT", 9),
        ("TMT", 5),
        ("TOST", 14),
        ("TOT", 13),
        ("TRT", 3),
        ("TVT", 12),
        ("U", -8),
        ("ULAST", 9),
        ("ULAT", 8),
        ("UTC", 0),
        ("UYST", -2),
        ("UYT", -3),
        ("UZT", 5),
        ("V", -9),
        ("VET", -4),
        ("VLAST", 11),
        ("VLAT", 10),
        ("VOST", 6),
        ("VUT", 11),
        ("W", -10),
        ("WAKT", 12),
        ("WARST", -3),
        ("WAST", 2),
        ("WAT", 1),
        ("WEST", 1),
        ("WET", 0),
        ("WFT", 12),
        ("WGST", -2),
        ("WGT", -3),
        ("WIB", 7),
        ("WIT", 9),
        ("WITA", 8),
        ("WST", 14),
        ("WT", 0),
        ("X", -11),
        ("Y", -12),
        ("YAKST", 10),
        ("YAKT", 9),
        ("YAPT", 10),
        ("YEKST", 6),
        ("YEKT", 5),
        ("Z", 0),
    )
}


@functools.singledispatch
def parse_date(value: str | datetime | date | None) -> datetime | None:
    """Parses a date string or object and returns a timezone-aware datetime object.

    If datetime passed will return the same instance with timezone awareness if not
    already present.

    Invalid inputs will return None.

    Returns:
        timezone-aware datetime or None if invalid value.
    """
    return None


@parse_date.register
def _(value: datetime) -> datetime | None:
    try:
        return value if is_aware(value) else make_aware(value)
    except ValueError:
        # weird offset: try and rebuild as UTC
        return make_aware(
            datetime(
                year=value.year,
                month=value.month,
                day=value.day,
                hour=value.hour,
                minute=value.minute,
                second=value.second,
            )
        )


@parse_date.register
def _(value: date) -> datetime | None:
    return parse_date(datetime.combine(value, datetime.min.time()))


@parse_date.register
def _(value: str) -> datetime | None:

    try:
        return (
            parse_date(date_parser.parse(value, tzinfos=_TZ_INFOS)) if value else None
        )
    except date_parser.ParserError:
        return None