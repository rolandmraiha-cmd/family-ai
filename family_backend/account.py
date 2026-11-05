"""Read-only, cached RunPod account figures; separate from admission estimates."""
import asyncio
import copy
from datetime import datetime, timezone
import math
import time

from family_backend.control import configured_runpod_key


def account_amount(value, negative=False):
    if type(value) not in {int, float} or not math.isfinite(value) or (not negative and value < 0):
        raise ValueError("Missing or invalid provider amount")
    return value


class RunPodAccount:
    refresh_seconds = 60

    def __init__(self, fetch=None, clock=time.time):
        self.fetch = fetch or self._fetch
        self.clock = clock
        self.lock = asyncio.Lock()
        self.checked_at = None
        self.window = None
        self.values = {}

    async def _fetch(self, part):
        import aiohttp
        key = await configured_runpod_key()
        if not key:
            raise ValueError("Existing provider credential unavailable")
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10), trust_env=True,
                headers={"Authorization": "Bearer " + key}) as session:
            if part == "balance":
                response = await session.post("https://api.runpod.io/graphql", json={
                    "query": "query FamilyAccountBalance { myself { clientBalance currentSpendPerHr } }"})
            else:
                response = await session.get("https://api.runpod.io/v2/billing",
                    params={"bucketSize": part, "lastN": 1})
            async with response:
                if response.status != 200:
                    raise ValueError("Provider account access unavailable")
                return await response.json()

    async def get(self):
        async with self.lock:
            now = self.clock()
            window = datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%d")
            if self.checked_at is None or now - self.checked_at >= self.refresh_seconds or window != self.window:
                # Never label yesterday's/month's total as today's current total.
                for part, length in (("day", 10), ("month", 7)):
                    if self.window and self.window[:length] != window[:length]:
                        self.values.pop(part, None)
                self.window = window
                await asyncio.gather(*(self._update(part, now) for part in ("balance", "day", "month")))
                self.checked_at = self.clock()
            return {"currency": "USD", "scope": "RunPod account", "timezone": "UTC",
                    "refresh_seconds": self.refresh_seconds, "checked_at": self.checked_at,
                    "billing_may_lag": True, **copy.deepcopy(self.values)}

    async def _update(self, part, now):
        try:
            data = await self.fetch(part)
            if part == "balance":
                if data.get("errors"):
                    raise ValueError("Provider account query failed")
                wallet = data["data"]["myself"]
                value = {"amount_usd": account_amount(wallet["clientBalance"], negative=True)}
                rate = wallet.get("currentSpendPerHr")
                value["rate_usd_per_hour"] = account_amount(rate) if rate is not None else None
            else:
                metadata = data["metadata"]
                query = metadata["query"]
                start = datetime.fromisoformat(query["startTime"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(query["endTime"].replace("Z", "+00:00"))
                current = datetime.fromtimestamp(now, timezone.utc)
                if (query["bucketSize"] != part or start.tzinfo is None or end.tzinfo is None
                        or not start <= current < end):
                    raise ValueError("Provider billing window is not current")
                value = {"amount_usd": account_amount(metadata["totals"]["totalAmount"]),
                         "period_start": query["startTime"], "period_end": query["endTime"]}
            self.values[part] = {**value, "observed_at": now, "status": "fresh"}
        except Exception:
            # Provider bodies/exceptions can contain private details. Return no
            # raw error, never turn a missing amount into zero or erase last good data.
            previous = self.values.get(part, {})
            self.values[part] = {**previous, "status": "stale" if "amount_usd" in previous else "unavailable"}
