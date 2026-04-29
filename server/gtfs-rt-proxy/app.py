from __future__ import annotations

import logging
import os
import threading
import time

import requests
from flask import Flask, Response, abort, jsonify
from google.transit import gtfs_realtime_pb2

from schedule import Schedule

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("gtfs-rt-proxy")

_UPSTREAM_PROD_DEFAULT = (
    "https://trujillo-admin-storage.s3.us-east-1.amazonaws.com/"
    "driver/gtfsrt/pe-trujillo.proto"
)
_UPSTREAM_SIM_DEFAULT = "http://gtfs-rt-simulator:9000/pe-trujillo.proto"

SIMULATED = os.environ.get("SIMULATED", "false").lower() == "true"
UPSTREAM_URL = (
    os.environ.get("UPSTREAM_URL_SIM", _UPSTREAM_SIM_DEFAULT)
    if SIMULATED
    else os.environ.get(
        "UPSTREAM_URL_PROD",
        os.environ.get("UPSTREAM_URL", _UPSTREAM_PROD_DEFAULT),
    )
)
GTFS_PATH = os.environ.get("GTFS_PATH", "/app/data/trujillo.gtfs.zip")
CACHE_TTL = float(os.environ.get("CACHE_TTL", "5"))
UPSTREAM_TIMEOUT = float(os.environ.get("UPSTREAM_TIMEOUT", "10"))

log.info(
    "Proxy upstream mode: %s → %s",
    "SIMULATED" if SIMULATED else "PROD",
    UPSTREAM_URL,
)

schedule = Schedule(GTFS_PATH)

_cache_lock = threading.Lock()
_cache: dict = {"ts": 0.0, "body": b"", "stats": {}}

app = Flask(__name__)


def fetch_upstream() -> bytes:
    resp = requests.get(
        UPSTREAM_URL,
        timeout=UPSTREAM_TIMEOUT,
        headers={
            "Cache-Control": "no-cache, no-store, max-age=0",
            "Pragma": "no-cache",
        },
        params={"_": int(time.time() * 1000)},
    )
    resp.raise_for_status()
    return resp.content


def enrich(raw: bytes) -> tuple[bytes, dict]:
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(raw)
    rewritten = skipped_no_schedule = skipped_already_has_trip_id = no_trip = 0

    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue
        vp = entity.vehicle
        if not vp.HasField("trip"):
            no_trip += 1
            continue
        trip = vp.trip
        if trip.HasField("trip_id") and trip.trip_id:
            skipped_already_has_trip_id += 1
            continue
        if not (trip.HasField("route_id") and trip.HasField("direction_id") and trip.HasField("start_time")):
            skipped_no_schedule += 1
            continue

        match = schedule.match(trip.route_id, trip.direction_id, trip.start_time)
        if match is None:
            skipped_no_schedule += 1
            continue

        matched_trip_id, aligned = match
        trip.trip_id = matched_trip_id
        trip.start_time = aligned

        if vp.HasField("vehicle"):
            vdesc = vp.vehicle
            if not (vdesc.HasField("id") and vdesc.id) and vdesc.HasField("license_plate") and vdesc.license_plate:
                vdesc.id = vdesc.license_plate

        rewritten += 1

    stats = {
        "entities": len(feed.entity),
        "rewritten": rewritten,
        "skipped_no_schedule": skipped_no_schedule,
        "skipped_already_has_trip_id": skipped_already_has_trip_id,
        "entities_without_trip": no_trip,
    }
    return feed.SerializeToString(), stats


def get_enriched_body() -> bytes:
    with _cache_lock:
        now = time.time()
        if _cache["body"] and (now - _cache["ts"]) < CACHE_TTL:
            return _cache["body"]

        raw = fetch_upstream()
        body, stats = enrich(raw)
        _cache["ts"] = now
        _cache["body"] = body
        _cache["stats"] = stats
        log.info("enriched: %s", stats)
        return body


@app.route("/gtfsrt.proto")
def gtfsrt_proto():
    try:
        body = get_enriched_body()
    except requests.RequestException as e:
        log.error("upstream fetch failed: %s", e)
        abort(502, description=f"Upstream error: {e}")
    return Response(body, mimetype="application/octet-stream")


@app.route("/healthz")
def healthz():
    return jsonify(
        {
            "status": "ok",
            "schedules_loaded": schedule.route_count,
            "last_cache_age_s": round(time.time() - _cache["ts"], 2) if _cache["ts"] else None,
            "last_stats": _cache.get("stats") or None,
        }
    )


@app.route("/")
def index():
    return jsonify(
        {
            "service": "gtfs-rt-proxy",
            "endpoints": ["/gtfsrt.proto", "/healthz"],
            "simulated": SIMULATED,
            "upstream": UPSTREAM_URL,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
