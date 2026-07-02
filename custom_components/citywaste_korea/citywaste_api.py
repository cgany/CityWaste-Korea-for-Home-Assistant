"""API helper for CityWaste Korea."""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

import requests
import urllib3

from .const import BASE_URL, REFERER

_LOGGER = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CityWasteApiError(Exception):
    """Raised when CityWaste API fetch fails."""


class CityWasteClient:
    """Synchronous CityWaste Korea client."""

    def __init__(self, tagprintcd: str, aptdong: int, apthono: int) -> None:
        self.tagprintcd = tagprintcd
        self.aptdong = aptdong
        self.apthono = apthono

    def fetch_month_data(self) -> dict[str, Any]:
        """Fetch this month's CityWaste data."""
        total_kg = 0.0
        last_kg = 0.0
        last_date = "-"
        address = "-"
        total_count = 0
        total_page_count = 0

        now = dt.datetime.now()
        first_date = now.strftime("%Y%m01")
        now_date = now.strftime("%Y%m%d")

        api_url = (
            f"{BASE_URL}?tagprintcd={self.tagprintcd}"
            f"&aptdong={self.aptdong}"
            f"&apthono={self.apthono}"
            f"&startchdate={first_date}"
            f"&endchdate={now_date}"
        )
        headers = {"Referer": REFERER}

        first_payload = self._request_json(f"{api_url}&pageIndex=1", headers)

        try:
            total_count = int(first_payload.get("totalCnt", 0))
            total_page_count = int(
                first_payload.get("paginationInfo", {}).get("totalPageCount", 0)
            )
            address = first_payload.get("ctznnm") or "-"
            rows = first_payload.get("list") or []

            if total_count > 0 and rows:
                last_kg = float(rows[0].get("qtyvalue", 0) or 0)
                last_date = rows[0].get("dttime") or "-"
                total_kg += sum(float(row.get("qtyvalue", 0) or 0) for row in rows)
        except (TypeError, ValueError, KeyError) as err:
            raise CityWasteApiError(f"Error parsing first response: {err}") from err

        for current_page in range(2, total_page_count + 1):
            payload = self._request_json(f"{api_url}&pageIndex={current_page}", headers)
            try:
                rows = payload.get("list") or []
                total_kg += sum(float(row.get("qtyvalue", 0) or 0) for row in rows)
            except (TypeError, ValueError, KeyError) as err:
                raise CityWasteApiError(
                    f"Error parsing page {current_page} response: {err}"
                ) from err

        _LOGGER.debug(
            "CityWaste fetched: total_kg=%s total_count=%s last_kg=%s",
            total_kg,
            total_count,
            last_kg,
        )

        return {
            "total_count": total_count,
            "last_kg": last_kg,
            "last_date": last_date,
            "total_kg": total_kg,
            "address": address,
        }

    def _request_json(self, url: str, headers: dict[str, str]) -> dict[str, Any]:
        _LOGGER.debug("CityWaste request URL: %s", url)
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as err:
            raise CityWasteApiError(f"Request failed: {err}") from err
        except ValueError as err:
            raise CityWasteApiError(f"JSON parse failed: {err}") from err
