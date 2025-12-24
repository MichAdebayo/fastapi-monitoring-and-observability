#!/usr/bin/env python3
"""Simple seed worker that performs randomized CRUD against the API.

Config via env:
  API_BASE (default: http://api:3030/items)
  INTERVAL_S (default: 2)
  CYCLE_S (seconds per run; default: 60)
  SEED (optional int)
  WORKER_ID (optional string)
  AUTH_TOKEN (optional bearer token)

Behaviour: runs for CYCLE_S seconds performing a random operation every INTERVAL_S
and then performs final diagnostics (list all items, sample of specific items).
"""

from __future__ import annotations

import contextlib
import os
import random
import time
import logging
from typing import List

import httpx
from faker import Faker

API_BASE = os.getenv("API_BASE", "http://api:3030/items").rstrip("/")
INTERVAL_S = float(os.getenv("INTERVAL_S", os.getenv("NTERVAL_S", "2")))
CYCLE_S = int(os.getenv("CYCLE_S", "60"))
SEED = os.getenv("SEED")
WORKER_ID = os.getenv("WORKER_ID", "seed-1")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
API_WAIT_TIMEOUT = int(os.getenv("API_WAIT_TIMEOUT", "60"))
API_WAIT_INTERVAL = float(os.getenv("API_WAIT_INTERVAL", "1.0"))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
logger = logging.getLogger("seed-worker")

fake = Faker()
if SEED:
    try:
        seed_int = int(SEED)
    except Exception:
        seed_int = abs(hash(SEED)) % (2**32)
    random.seed(seed_int)
    Faker.seed(seed_int)


def headers() -> dict[str, str]:
    h = {"Content-Type": "application/json"}
    if AUTH_TOKEN:
        h["Authorization"] = f"Bearer {AUTH_TOKEN}"
    return h


def create_item(client: httpx.Client) -> int | None:
    payload = {"nom": fake.word(), "prix": round(random.uniform(1, 500), 2)}
    try:
        r = client.post(API_BASE, json=payload, headers=headers(), timeout=10.0)
        if r.status_code in (200, 201):
            data = r.json()
            item_id = data.get("id")
            logger.info(
                "created id=%s payload=%s status=%s", item_id, payload, r.status_code
            )
            return item_id
        else:
            logger.warning("create failed status=%s text=%s", r.status_code, r.text)
    except Exception as exc:
        logger.error("create exception: %s", exc)
    return None


def get_items(client: httpx.Client, params: dict | None = None) -> List[dict]:
    try:
        r = client.get(API_BASE, params=params or {}, headers=headers(), timeout=10.0)
        if r.status_code == 200:
            data = r.json()
            logger.info("fetched %d items", len(data) if isinstance(data, list) else 0)
            return data
        else:
            logger.warning("list failed status=%s", r.status_code)
    except Exception as exc:
        logger.error("list exception: %s", exc)
    return []


def get_item(client: httpx.Client, item_id: int) -> dict | None:
    try:
        r = client.get(f"{API_BASE}/{item_id}", headers=headers(), timeout=10.0)
        if r.status_code == 200:
            logger.info("got item id=%s", item_id)
            return r.json()
        else:
            logger.debug("get item %s failed status=%s", item_id, r.status_code)
    except Exception as exc:
        logger.error("get item exception: %s", exc)
    return None


def update_item(client: httpx.Client, item_id: int) -> bool:
    payload = {}
    if random.random() < 0.5:
        payload["nom"] = fake.word()
    if random.random() < 0.8:
        payload["prix"] = round(random.uniform(1, 500), 2)
    try:
        r = client.put(
            f"{API_BASE}/{item_id}", json=payload, headers=headers(), timeout=10.0
        )
        if r.status_code == 200:
            logger.info("updated id=%s payload=%s", item_id, payload)
            return True
        else:
            logger.warning("update failed id=%s status=%s", item_id, r.status_code)
    except Exception as exc:
        logger.error("update exception: %s", exc)
    return False


def delete_item(client: httpx.Client, item_id: int) -> bool:
    try:
        r = client.delete(f"{API_BASE}/{item_id}", headers=headers(), timeout=10.0)
        if r.status_code in (200, 204):
            logger.info("deleted id=%s status=%s", item_id, r.status_code)
            return True
        else:
            logger.warning("delete failed id=%s status=%s", item_id, r.status_code)
    except Exception as exc:
        logger.error("delete exception: %s", exc)
    return False


def choose_op(created_ids: List[int]) -> str:
    # Higher probability for create so DB grows; some reads/updates/deletes to exercise metrics
    ops = ["create", "list", "get", "update", "delete"]
    weights = [0.4, 0.2, 0.15, 0.15, 0.1]
    return random.choices(ops, weights=weights, k=1)[0]


def main() -> None:
    logger.info(
        "seed-worker starting (worker_id=%s) -> api=%s interval=%s cycle=%s",
        WORKER_ID,
        API_BASE,
        INTERVAL_S,
        CYCLE_S,
    )
    # wait for API health endpoint before starting operations to avoid "connection refused"
    health_url = API_BASE.split("/items")[0] + "/health"

    def wait_for_api(
        client: httpx.Client, timeout: int = 60, interval: float = 1.0
    ) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            try:
                r = client.get(health_url, headers=headers(), timeout=3.0)
                if r.status_code == 200:
                    logger.info("API health check passed: %s", health_url)
                    return True
                logger.info("API health returned status %s, retrying...", r.status_code)
            except Exception:
                logger.info("API not reachable at %s, retrying...", health_url)
            time.sleep(interval)
        logger.error("API did not become healthy within %s seconds", timeout)
        return False

    created_ids: List[int] = []
    backoff = 1.0
    start = time.time()
    end = start + CYCLE_S if CYCLE_S > 0 else float("inf")

    # Follow redirects (FastAPI may redirect paths without trailing slash -> 307)
    with httpx.Client(follow_redirects=True) as client:
        # ensure API is ready before starting operations (configurable)
        if not wait_for_api(
            client, timeout=API_WAIT_TIMEOUT, interval=API_WAIT_INTERVAL
        ):
            logger.error("Aborting worker because API is not healthy")
            return
        while time.time() < end:
            op = choose_op(created_ids)
            try:
                if op == "create":
                    item_id = create_item(client)
                    if item_id:
                        created_ids.append(item_id)
                        backoff = 1.0
                elif op == "list":
                    _ = get_items(client)
                elif op == "get":
                    if created_ids:
                        _ = get_item(client, random.choice(created_ids))
                    else:
                        _ = get_items(client, params={"skip": 0, "limit": 10})
                elif op == "update":
                    if created_ids:
                        update_item(client, random.choice(created_ids))
                elif op == "delete":
                    if created_ids:
                        item_id = random.choice(created_ids)
                        if delete_item(client, item_id):
                            with contextlib.suppress(ValueError):
                                created_ids.remove(item_id)
                # reset backoff on success path; if we reach here assume success-ish
                time.sleep(INTERVAL_S)
            except Exception as exc:
                logger.exception("Unexpected worker exception: %s", exc)
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)

        # end of cycle - diagnostics
        logger.info(
            "Cycle complete - performing diagnostics: fetch all items and sample specific items"
        )
        all_items = get_items(client)
        ids = [i.get("id") for i in all_items if i and i.get("id") is not None]
        # Filter out None values to ensure only int IDs are used
        valid_ids = [i for i in ids if isinstance(i, int)]
        if valid_ids:
            sample_k = min(5, len(valid_ids))
            sample_ids = random.sample(valid_ids, sample_k)
        else:
            sample_ids = []
        for sid in sample_ids:
            get_item(client, sid)

    logger.info("seed-worker finished")


if __name__ == "__main__":
    main()
