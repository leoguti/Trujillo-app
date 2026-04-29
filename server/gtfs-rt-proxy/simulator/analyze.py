#!/usr/bin/env python3
"""Analyze a directory of recorded GTFS-RT .proto files and emit a compact
patterns.json that the simulator replays with current dates/times.

Usage:
    python analyze.py --history ../../GTFS-RT/history/ --out patterns.json
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from google.transit import gtfs_realtime_pb2


_TS_RE = re.compile(r"(\d{8}T\d{6}Z)\.proto$")


def _parse_file_ts(name: str):
    m = _TS_RE.search(name)
    if not m:
        return None
    return datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)


def _mode(values):
    c = Counter(values)
    return c.most_common(1)[0][0]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--history", required=True, help="Directory with .proto files")
    p.add_argument("--out", default="patterns.json", help="Output JSON path")
    p.add_argument(
        "--min-duration",
        type=int,
        default=60,
        help="Discard trajectories shorter than this many seconds",
    )
    p.add_argument(
        "--sample-interval",
        type=int,
        default=5,
        help="Sample one point every N seconds along each trajectory",
    )
    args = p.parse_args()

    history_dir = Path(args.history)
    files = sorted(f for f in history_dir.glob("*.proto") if _parse_file_ts(f.name))
    if not files:
        raise SystemExit(f"No .proto files matched in {history_dir}")

    # (licensePlate, startDate, startTime) -> list of observations
    trips: dict[tuple, list] = defaultdict(list)

    feed = gtfs_realtime_pb2.FeedMessage()
    for f in files:
        file_ts = _parse_file_ts(f.name)
        feed.Clear()
        try:
            feed.ParseFromString(f.read_bytes())
        except Exception:
            continue
        for entity in feed.entity:
            if not entity.HasField("vehicle"):
                continue
            v = entity.vehicle
            if not v.HasField("trip") or not v.HasField("position"):
                continue
            trip = v.trip
            plate = v.vehicle.license_plate if v.HasField("vehicle") else ""
            if not plate or not trip.HasField("route_id"):
                continue
            key = (plate, trip.start_date, trip.start_time)
            ts = (
                datetime.fromtimestamp(v.timestamp, timezone.utc)
                if v.timestamp
                else file_ts
            )
            trips[key].append(
                {
                    "ts": ts,
                    "lat": v.position.latitude,
                    "lon": v.position.longitude,
                    "heading": v.position.bearing
                    if v.position.HasField("bearing")
                    else 0.0,
                    "route_id": trip.route_id,
                    "direction_id": int(trip.direction_id),
                }
            )

    trajectories = []
    for key, points in trips.items():
        points.sort(key=lambda p: p["ts"])
        # Dedupe consecutive duplicates (same ts)
        deduped = [points[0]]
        for p in points[1:]:
            if p["ts"] != deduped[-1]["ts"]:
                deduped.append(p)
        points = deduped

        if len(points) < 3:
            continue

        duration = (points[-1]["ts"] - points[0]["ts"]).total_seconds()
        if duration < args.min_duration:
            continue

        route_id = _mode([p["route_id"] for p in points])
        direction_id = _mode([p["direction_id"] for p in points])

        # Uniform sampling every `sample_interval` seconds using nearest-neighbor
        # on recorded points — simple and robust for irregular inputs.
        start_ts = points[0]["ts"].timestamp()
        sampled = []
        t = 0
        idx = 0
        while t <= duration:
            target = start_ts + t
            while (
                idx < len(points) - 1
                and abs(points[idx + 1]["ts"].timestamp() - target)
                < abs(points[idx]["ts"].timestamp() - target)
            ):
                idx += 1
            p = points[idx]
            sampled.append(
                {
                    "t": t,
                    "lat": round(p["lat"], 6),
                    "lon": round(p["lon"], 6),
                    "heading": round(p["heading"], 1),
                }
            )
            t += args.sample_interval

        if len(sampled) < 3:
            continue

        trajectories.append(
            {
                "route_id": route_id,
                "direction_id": direction_id,
                "duration_seconds": int(duration),
                "sample_plate": key[0],
                "points": sampled,
            }
        )

    output = {
        "source": {
            "history_dir": str(history_dir),
            "files_analyzed": len(files),
            "span_utc": [
                _parse_file_ts(files[0].name).isoformat().replace("+00:00", "Z"),
                _parse_file_ts(files[-1].name).isoformat().replace("+00:00", "Z"),
            ],
            "generated_at_utc": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "trajectories_kept": len(trajectories),
            "min_duration_seconds": args.min_duration,
            "sample_interval_seconds": args.sample_interval,
        },
        "trajectories": trajectories,
    }

    Path(args.out).write_text(json.dumps(output, indent=2))
    print(
        f"Wrote {args.out}: {len(trajectories)} trajectories from {len(files)} files"
    )
    route_counts = Counter((t["route_id"], t["direction_id"]) for t in trajectories)
    for (route, dir_), count in route_counts.most_common():
        print(f"  route={route} dir={dir_}: {count}")


if __name__ == "__main__":
    main()
