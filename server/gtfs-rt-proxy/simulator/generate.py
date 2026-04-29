import random
import string
from dataclasses import dataclass
from datetime import datetime, timezone

from google.transit import gtfs_realtime_pb2


@dataclass
class ClonedTrajectory:
    route_id: str
    direction_id: int
    points: list
    duration: float
    plate: str
    spawn_ts: float


def _random_plate(rng: random.Random) -> str:
    letters = "".join(rng.choices(string.ascii_uppercase, k=3))
    digits = "".join(rng.choices(string.digits, k=4))
    return f"{letters}-{digits}"


def build_pool(patterns: dict, clone_factor: int, server_start: datetime, seed: int = 42) -> list:
    rng = random.Random(seed)
    pool: list[ClonedTrajectory] = []
    start_ts = server_start.timestamp()

    for idx, traj in enumerate(patterns["trajectories"]):
        for clone in range(clone_factor):
            plate = traj["sample_plate"] if clone == 0 else _random_plate(rng)
            # Stagger spawn by arbitrary offset inside duration so clones are
            # at different stages of the trajectory from the start.
            offset = rng.uniform(0, traj["duration_seconds"])
            pool.append(
                ClonedTrajectory(
                    route_id=traj["route_id"],
                    direction_id=int(traj["direction_id"]),
                    points=traj["points"],
                    duration=float(traj["duration_seconds"]),
                    plate=plate,
                    spawn_ts=start_ts - offset,
                )
            )
    return pool


def _interpolate(points: list, t: float) -> tuple[float, float, float]:
    if t <= points[0]["t"]:
        p = points[0]
        return (p["lat"], p["lon"], p["heading"])
    if t >= points[-1]["t"]:
        p = points[-1]
        return (p["lat"], p["lon"], p["heading"])
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        if a["t"] <= t <= b["t"]:
            span = b["t"] - a["t"]
            ratio = (t - a["t"]) / span if span > 0 else 0.0
            lat = a["lat"] + (b["lat"] - a["lat"]) * ratio
            lon = a["lon"] + (b["lon"] - a["lon"]) * ratio
            # Linear heading interpolation is fine for short hops; we sample
            # every few seconds so the wrap-around error is negligible.
            heading = a["heading"] + (b["heading"] - a["heading"]) * ratio
            return (lat, lon, heading)
    p = points[-1]
    return (p["lat"], p["lon"], p["heading"])


def build_feed(pool: list, now: datetime) -> bytes:
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"
    feed.header.incrementality = gtfs_realtime_pb2.FeedHeader.FULL_DATASET
    feed.header.timestamp = int(now.timestamp())

    now_ts = now.timestamp()
    for c in pool:
        elapsed = now_ts - c.spawn_ts
        if elapsed < 0:
            continue
        loop_idx = int(elapsed // c.duration)
        t_in_traj = elapsed - loop_idx * c.duration
        lat, lon, heading = _interpolate(c.points, t_in_traj)

        this_run_start_ts = c.spawn_ts + loop_idx * c.duration
        this_run_start = datetime.fromtimestamp(this_run_start_ts, timezone.utc)

        entity = feed.entity.add()
        entity.id = f"{c.plate}-{loop_idx}"
        v = entity.vehicle
        v.trip.route_id = c.route_id
        v.trip.direction_id = c.direction_id
        v.trip.start_date = this_run_start.strftime("%Y%m%d")
        v.trip.start_time = this_run_start.strftime("%H:%M:%S")
        v.position.latitude = lat
        v.position.longitude = lon
        v.position.bearing = heading
        v.timestamp = int(now_ts)
        v.vehicle.license_plate = c.plate

    return feed.SerializeToString()
