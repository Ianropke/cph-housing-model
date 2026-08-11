"""Small client for Finans Danmarks legacy Statistikbank tables.

The site has no JSON API, but its public table form is stable and produces a
server-side PX table.  This client deliberately preserves the source period and
query metadata so callers cannot present an old or failed observation as live.
"""
from __future__ import annotations

import datetime as dt
import html
import re
import time
import urllib.parse
from curl_cffi import requests


BASE_URL = "https://rkr.statistikbank.dk/statbank5a"


def _get(url: str, data: dict | None = None) -> str:
    # curl_cffi uses the system trust store in the GitHub/Vercel runners and
    # handles the corporate TLS proxy used during local development. The legacy
    # RKR form occasionally resets a burst of connections, so retrying is safe:
    # the requests are read-only and a failed fetch never has a fallback value.
    last_error = None
    for attempt in range(3):
        try:
            response = requests.post(url, data=data, impersonate="chrome110", timeout=30) if data else requests.get(
                url, impersonate="chrome110", timeout=30
            )
            response.raise_for_status()
            return response.content.decode("iso-8859-1")
        except Exception as error:
            last_error = error
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"RKR request failed after 3 attempts: {last_error}")


def _input_value(page: str, name: str) -> str:
    match = re.search(rf'<input[^>]+name="{re.escape(name)}"[^>]+value="([^"]*)"', page, re.I)
    if not match:
        raise ValueError(f"Missing RKR form field: {name}")
    return html.unescape(match.group(1))


def _latest_period(page: str, position: int) -> str:
    block = re.search(rf'<SELECT[^>]+NAME="var{position}"[^>]*>(.*?)</SELECT>', page, re.I | re.S)
    if not block:
        raise ValueError("RKR table has no time selector")
    selected = re.search(r'<OPTION VALUE="([^"]+)" selected>', block.group(1), re.I)
    if not selected:
        raise ValueError("RKR table has no selected latest period")
    return html.unescape(selected.group(1))


def fetch_scalar(table: str, selections: dict[int, str], period: str | None = None) -> dict:
    """Fetch one official Statistikbank observation for a table selection."""
    definition_url = f"{BASE_URL}/SelectVarVal/Define.asp?MainTable={urllib.parse.quote(table)}&PLanguage=0"
    page = _get(definition_url)
    count = int(_input_value(page, "antvar"))
    time_position = next(
        position for position in range(1, count + 1) if _input_value(page, f"V{position}") == "Tid"
    )
    selections = {**selections, time_position: period or _latest_period(page, time_position)}
    subject_code = _input_value(page, "SubjectCode")
    contents = _input_value(page, "Contents")
    time_label = _input_value(page, "tidrubr")

    payload = {
        "TS": f"ShowTable&OldTab=SELECT&SubjectCode={subject_code}&AntVar={count}&Contents={contents}&tidrubr={time_label}",
        "PLanguage": "0", "FF": "20", "OldTab": "SELECT", "SavePXSId": "0",
        "MainTable": table, "SubTable": _input_value(page, "SubTable"), "SelCont": _input_value(page, "SelCont"),
        "Contents": contents, "SubjectCode": subject_code, "SubjectArea": _input_value(page, "SubjectArea"),
        "antvar": str(count), "action": "urval", "guest": "-1", "GuestFileSize": _input_value(page, "GuestFileSize"),
        "MaxFileSize": _input_value(page, "MaxFileSize"), "tidrubr": time_label,
        "tfrequency": _input_value(page, "tfrequency"), "Forward.x": "60", "Forward.y": "16",
    }
    for position in range(1, count + 1):
        for prefix in ("V", "VS", "VP"):
            payload[f"{prefix}{position}"] = _input_value(page, f"{prefix}{position}")
        payload[f"var{position}"] = selections[position]

    output = _get(f"{BASE_URL}/SelectVarVal/saveselections.asp", payload)
    value = re.search(r'<td class=No>\s*([^<]+?)\s*</td>', output, re.I)
    if not value:
        raise ValueError(f"RKR {table} returned no observation")
    numeric = float(value.group(1).replace(" ", "").replace(".", "").replace(",", "."))
    return {
        "table": table,
        "value": numeric,
        "period": selections[time_position],
        "source": "Finans Danmark Statistikbank",
        "source_url": definition_url,
        "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "live",
    }
