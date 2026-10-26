import uuid
import logging
from datetime import date, datetime, timedelta
from typing import Any
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class ElexonFetchError(RuntimeError):
    """Raised when Elexon BMRS returns an error, so ingestion fails loudly instead of storing partial data."""


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ElexonService:
    """
    Client for the Elexon BMRS dataset streams used by the platform:
    - FUELHH  (fuelType WIND): metered half-hourly national wind generation (actuals)
    - WINDFOR: national wind generation forecasts, one curve per publishTime

    Only real Elexon data is ever returned. Any HTTP failure raises ElexonFetchError.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.base_url = base_url or settings.ELEXON_BASE_URL
        self.api_key = api_key or settings.ELEXON_API_KEY
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.transport = transport

    @staticmethod
    def calculate_settlement_period(dt: datetime) -> int:
        """
        Settlement Period (1 to 48) for a UTC timestamp.
        Valid for January, when UK local time (GMT) equals UTC. Elexon's own
        settlementPeriod field is preferred whenever the payload provides it.
        """
        return (dt.hour * 2) + (dt.minute // 30) + 1

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=self.timeout, transport=self.transport)

    async def _get(self, client: httpx.AsyncClient, url: str, params: dict[str, str]) -> list[dict[str, Any]]:
        if self.api_key:
            params = {**params, "api_key": self.api_key}
        response = await client.get(url, params=params)
        if response.status_code != 200:
            raise ElexonFetchError(f"GET {url} {params} returned HTTP {response.status_code}")
        data = response.json()
        return data if isinstance(data, list) else data.get("data", [])

    async def fetch_actual_wind(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        """
        Fetches metered WIND generation for settlement dates start_date..end_date (inclusive).
        Deduplicated on startTime.
        """
        url = f"{self.base_url}/datasets/FUELHH/stream"
        by_start: dict[datetime, dict[str, Any]] = {}

        async with self._client() as client:
            curr = start_date
            while curr <= end_date:
                chunk_end = min(curr + timedelta(days=6), end_date)
                items = await self._get(client, url, {
                    "settlementDateFrom": curr.isoformat(),
                    "settlementDateTo": chunk_end.isoformat(),
                    "fuelType": "WIND",
                })
                for item in items:
                    if str(item.get("fuelType", "")).upper() != "WIND":
                        continue
                    st = _parse_utc(item["startTime"])
                    by_start[st] = {
                        "id": uuid.uuid4(),
                        "start_time": st,
                        "settlement_period": int(item.get("settlementPeriod") or self.calculate_settlement_period(st)),
                        "generation": float(item["generation"]),
                    }
                curr = chunk_end + timedelta(days=1)

        records = sorted(by_start.values(), key=lambda r: r["start_time"])
        logger.info("Fetched %d actual wind records from Elexon FUELHH.", len(records))
        return records

    async def fetch_forecast_wind(self, publish_from: datetime, publish_to: datetime) -> list[dict[str, Any]]:
        """
        Fetches every WINDFOR forecast published in [publish_from, publish_to).
        WINDFOR points are hourly; each one is also applied to the following half-hour
        (a step hold), so every half-hourly actual has a comparable forecast value.
        Deduplicated on (startTime, publishTime).
        """
        url = f"{self.base_url}/datasets/WINDFOR/stream"
        by_key: dict[tuple[datetime, datetime], dict[str, Any]] = {}

        def add(st: datetime, pt: datetime, gen: float) -> None:
            by_key[(st, pt)] = {
                "id": uuid.uuid4(),
                "start_time": st,
                "publish_time": pt,
                "settlement_period": self.calculate_settlement_period(st),
                "generation": gen,
            }

        async with self._client() as client:
            curr = publish_from
            while curr < publish_to:
                chunk_end = min(curr + timedelta(days=1), publish_to)
                items = await self._get(client, url, {
                    "publishDateTimeFrom": curr.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "publishDateTimeTo": chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                })
                for item in items:
                    st = _parse_utc(item["startTime"])
                    pt = _parse_utc(item["publishTime"])
                    # The API's publish window is inclusive at both ends; keep [from, to) to avoid double counting.
                    if not (curr <= pt < chunk_end):
                        continue
                    gen = float(item["generation"])
                    add(st, pt, gen)
                    if st.minute == 0:
                        half_hour = st + timedelta(minutes=30)
                        # Never overwrite a genuine half-hourly value with a step-held one.
                        by_key.setdefault((half_hour, pt), {
                            "id": uuid.uuid4(),
                            "start_time": half_hour,
                            "publish_time": pt,
                            "settlement_period": self.calculate_settlement_period(half_hour),
                            "generation": gen,
                        })
                curr = chunk_end

        records = sorted(by_key.values(), key=lambda r: (r["start_time"], r["publish_time"]))
        logger.info("Fetched %d wind forecast records from Elexon WINDFOR.", len(records))
        return records
