#!/usr/bin/env python3
"""
Candid text parser for ``icp canister call --json`` responses.

``icp canister call --candid <did> --json`` produces:
    {"response_bytes": "<hex>", "response_candid": "(<candid text>)"}

This module parses ``response_candid`` into Python objects.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional


def find_candid_file(canister: str, realm_folder: str) -> Optional[str]:
    """Return the absolute path of the .did file for `canister` from dfx.json."""
    dfx_json = os.path.join(realm_folder, "dfx.json")
    try:
        with open(dfx_json) as f:
            dfx = json.load(f)
        candid_rel = dfx.get("canisters", {}).get(canister, {}).get("candid", "")
        if not candid_rel:
            return None
        if not os.path.isabs(candid_rel):
            candid_rel = os.path.join(realm_folder, candid_rel)
        return candid_rel if os.path.exists(candid_rel) else None
    except Exception:
        return None


class _CandidParser:
    """Recursive-descent parser for Candid text format (as produced by icp-cli)."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self._skip()

    def _skip(self) -> None:
        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch in " \t\n\r":
                self.pos += 1
            elif self.text[self.pos : self.pos + 2] == "//":
                while self.pos < len(self.text) and self.text[self.pos] != "\n":
                    self.pos += 1
            else:
                break

    def _peek(self) -> Optional[str]:
        return self.text[self.pos] if self.pos < len(self.text) else None

    def _consume(self, s: str) -> bool:
        if self.text[self.pos : self.pos + len(s)] == s:
            self.pos += len(s)
            self._skip()
            return True
        return False

    def _expect(self, s: str) -> None:
        if not self._consume(s):
            snippet = self.text[self.pos : self.pos + 20]
            raise ValueError(f"Expected {s!r} at pos {self.pos}, got {snippet!r}")

    def _keyword(self, kw: str) -> bool:
        end = self.pos + len(kw)
        if self.text[self.pos : end] != kw:
            return False
        if end < len(self.text) and (self.text[end].isalnum() or self.text[end] == "_"):
            return False
        return True

    def parse(self) -> Any:
        self._expect("(")
        values: list[Any] = []
        while self._peek() != ")" and self._peek() is not None:
            values.append(self._value())
            self._consume(",")
        self._expect(")")
        return values[0] if len(values) == 1 else values

    def _value(self) -> Any:
        p = self._peek()
        if p is None:
            return None

        if self._keyword("record"):
            return self._record()
        if self._keyword("variant"):
            return self._variant()
        if self._keyword("vec"):
            return self._vec()
        if self._keyword("opt"):
            self._consume("opt")
            return self._value()
        if self._keyword("null"):
            self._consume("null")
            return None
        if self._keyword("true"):
            self._consume("true")
            return True
        if self._keyword("false"):
            self._consume("false")
            return False
        if self._keyword("principal"):
            self._consume("principal")
            return self._string()
        if self._keyword("blob"):
            self._consume("blob")
            return self._string()
        if self._keyword("func"):
            self._consume("func")
            return self._string()
        if self._keyword("service"):
            self._consume("service")
            return self._string()
        if p == '"':
            return self._string()
        if p in "0123456789" or (
            p in "+-" and self.pos + 1 < len(self.text) and self.text[self.pos + 1].isdigit()
        ):
            return self._number()
        if p == "(":
            self._consume("(")
            v = self._value()
            self._consume(")")
            return v
        if p.isalpha() or p == "_":
            return self._ident()
        return None

    def _record(self) -> dict:
        self._consume("record")
        self._expect("{")
        result: dict = {}
        while self._peek() != "}" and self._peek() is not None:
            key = self._key()
            self._expect("=")
            val = self._value()
            result[key] = val
            self._consume(";")
        self._expect("}")
        return result

    def _variant(self) -> dict:
        self._consume("variant")
        self._expect("{")
        key = self._key()
        if self._consume("="):
            val: Any = self._value()
        else:
            val = None
        self._consume(";")
        self._expect("}")
        return {key: val}

    def _vec(self) -> list:
        self._consume("vec")
        self._expect("{")
        items: list = []
        while self._peek() != "}" and self._peek() is not None:
            items.append(self._value())
            self._consume(";")
        self._expect("}")
        return items

    def _key(self) -> str:
        p = self._peek()
        if p and p.isdigit():
            start = self.pos
            while self.pos < len(self.text) and (
                self.text[self.pos].isdigit() or self.text[self.pos] == "_"
            ):
                self.pos += 1
            raw = self.text[start : self.pos].replace("_", "")
            self._skip()
            return f"_{raw}"
        return self._ident()

    def _ident(self) -> str:
        if not self._peek() or not (self._peek().isalpha() or self._peek() == "_"):
            return ""
        start = self.pos
        while self.pos < len(self.text) and (
            self.text[self.pos].isalnum() or self.text[self.pos] == "_"
        ):
            self.pos += 1
        ident = self.text[start : self.pos]
        self._skip()
        return ident

    def _string(self) -> str:
        self._expect('"')
        buf: list[str] = []
        while self.pos < len(self.text) and self.text[self.pos] != '"':
            ch = self.text[self.pos]
            if ch == "\\":
                self.pos += 1
                esc = self.text[self.pos]
                if esc == "n":
                    buf.append("\n")
                elif esc == "t":
                    buf.append("\t")
                elif esc == "r":
                    buf.append("\r")
                elif esc == '"':
                    buf.append('"')
                elif esc == "\\":
                    buf.append("\\")
                elif esc == "u":
                    self.pos += 1
                    self.pos += 1
                    hex_start = self.pos
                    while self.pos < len(self.text) and self.text[self.pos] != "}":
                        self.pos += 1
                    buf.append(chr(int(self.text[hex_start : self.pos], 16)))
                else:
                    buf.append(esc)
            else:
                buf.append(ch)
            self.pos += 1
        self.pos += 1
        self._skip()
        return "".join(buf)

    def _number(self) -> int | float:
        start = self.pos
        if self.text[self.pos] in "+-":
            self.pos += 1
        while self.pos < len(self.text) and (
            self.text[self.pos].isdigit() or self.text[self.pos] == "_"
        ):
            self.pos += 1
        is_float = False
        if self.pos < len(self.text) and self.text[self.pos] == ".":
            is_float = True
            self.pos += 1
            while self.pos < len(self.text) and self.text[self.pos].isdigit():
                self.pos += 1
        raw = self.text[start : self.pos].replace("_", "")
        self._skip()
        if self.pos < len(self.text) and self.text[self.pos] == ":":
            self.pos += 1
            self._skip()
            self._ident()
        return float(raw) if is_float else int(raw)


def parse_candid_response(envelope_json: str) -> Any:
    try:
        envelope = json.loads(envelope_json)
    except (json.JSONDecodeError, TypeError):
        return None

    candid_text = envelope.get("response_candid", "")
    if not candid_text:
        return None

    try:
        return _CandidParser(candid_text).parse()
    except Exception:
        return None


def candid_to_json(value: Any) -> str:
    def _default(o: Any) -> Any:
        return str(o)

    return json.dumps(value, default=_default)


def parse(candid_text: str) -> Any:
    try:
        return _CandidParser(candid_text).parse()
    except Exception:
        return None
