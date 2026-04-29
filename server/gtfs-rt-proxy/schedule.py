from __future__ import annotations

import bisect
import csv
import io
import logging
import zipfile

log = logging.getLogger(__name__)


def to_seconds(hms: str) -> int:
    h, m, s = hms.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


def to_hms(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds // 60) % 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


class Schedule:
    def __init__(self, gtfs_zip_path: str):
        self._entries: dict[tuple[str, int], list[tuple[str, list[int]]]] = {}
        self._load(gtfs_zip_path)

    @staticmethod
    def _read_csv(zf: zipfile.ZipFile, name: str):
        with zf.open(name) as f:
            return list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")))

    def _load(self, path: str) -> None:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            if "frequencies.txt" not in names:
                raise RuntimeError(
                    f"{path} has no frequencies.txt. "
                    "Use the non-expanded GTFS that still contains frequencies."
                )
            trips = self._read_csv(zf, "trips.txt")
            freqs = self._read_csv(zf, "frequencies.txt")

        trip_to_route_dir = {
            t["trip_id"]: (t["route_id"], int(t["direction_id"])) for t in trips
        }

        for f in freqs:
            trip_id = f["trip_id"]
            key = trip_to_route_dir.get(trip_id)
            if key is None:
                continue
            start = to_seconds(f["start_time"])
            end = to_seconds(f["end_time"])
            headway = int(f["headway_secs"])
            slots = list(range(start, end, headway))
            self._entries.setdefault(key, []).append((trip_id, slots))

        log.info(
            "Loaded schedules for %d (route_id, direction_id) pairs", len(self._entries)
        )

    @property
    def route_count(self) -> int:
        return len(self._entries)

    def match(
        self, route_id: str, direction_id: int, start_time_hms: str
    ) -> tuple[str, str] | None:
        entries = self._entries.get((route_id, int(direction_id)))
        if not entries:
            return None
        try:
            driver = to_seconds(start_time_hms)
        except ValueError:
            return None

        best_expanded_trip_id: str | None = None
        best_slot: int | None = None
        best_diff: int | None = None

        for base_trip_id, slots in entries:
            idx = bisect.bisect_left(slots, driver)
            for slot_idx in (idx - 1 if idx > 0 else None, idx if idx < len(slots) else None):
                if slot_idx is None:
                    continue
                slot = slots[slot_idx]
                diff = abs(slot - driver)
                if best_diff is None or diff < best_diff:
                    best_diff = diff
                    best_expanded_trip_id = f"{base_trip_id}{slot_idx:06d}"
                    best_slot = slot

        if best_expanded_trip_id is None or best_slot is None:
            return None
        return best_expanded_trip_id, to_hms(best_slot)
