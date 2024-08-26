#!/usr/bin/env python3

import json
from decimal import Decimal
import datetime


class NewJSONEncoder(json.JSONEncoder):
    def _encode_with_type(self, val: str, dtype: str):
        return "||%(dtype)s::%(val)s" % {"dtype": dtype, "val": val}

    def default(self, o):
        if isinstance(o, Decimal):
            return self._encode_with_type(str(o), "decimal")
        if isinstance(o, datetime.datetime):
            return self._encode_with_type(str(o), "datetime")
        if isinstance(o, datetime.date):
            return self._encode_with_type(str(o), "date")
        return super(NewJSONEncoder, self).default(o)


class NewJsonDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        """
        See: https://gist.github.com/setaou/ff98e82a9ce68f4c2b8637406b4620d1
        """
        json.JSONDecoder.__init__(self, *args, **kwargs)
        self.parse_string = self._custom_scanstring
        self.scan_once = json.scanner.py_make_scanner(self)

    def _custom_scanstring(self, s: str, end: int, strict: bool = True):
        """
        See: https://gist.github.com/setaou/ff98e82a9ce68f4c2b8637406b4620d1
        """
        s, end = json.decoder.scanstring(s, end, strict)
        new_s = self._handle_str(s)
        return (new_s, end)

    def _extract_parts(self, obj: str):
        if obj[0:2] != "||":
            return (None, obj)
        parts = obj.split("::", 1)
        dtype = parts[0][2:]
        val = "" if len(parts) == 1 else parts[1]
        return (dtype, val)

    def _decode_decimal(self, val: str):
        return Decimal(val)

    def _decode_datetime(self, val: str):
        return datetime.datetime.fromisoformat(val)

    def _decode_date(self, val: str):
        return datetime.date.fromisoformat(val)

    def _handle_str(self, obj: str):
        dtype, val = self._extract_parts(obj)
        if dtype == "datetime":
            return self._decode_datetime(val)
        if dtype == "date":
            return self._decode_date(val)
        if dtype == "decimal":
            return self._decode_decimal(val)
        return val
