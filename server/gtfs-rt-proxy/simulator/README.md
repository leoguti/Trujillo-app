# gtfs-rt-simulator

Produces a synthesized GTFS-Realtime vehicle-positions feed derived from a
previously recorded history of real driver-app publishes. Used by the
`gtfs-rt-proxy` as an alternative upstream so you can exercise OTP + the
mobile app without depending on live driver activity.

## How it works

```
ONE-TIME (local, when you record new history):

    GTFS-RT/history/*.proto  ──►  analyze.py  ──►  patterns.json
                                                   (committed, ~100 KB)

RUNTIME (inside the simulator container):

    patterns.json  ──►  generate.py  ──►  FeedMessage @ now  ──►  HTTP /pe-trujillo.proto
```

The output is formatted **exactly like the real driver-app feed** on S3:
no `trip_id`, vehicles identified by `license_plate`, with
`route_id + direction_id + start_date + start_time`. The proxy enriches it
downstream the same way it enriches the production feed.

## When to run `analyze.py`

Any time you have a fresh batch of recorded `.proto` files. The simulator
does **not** replay old dates — it interpolates recorded trajectories
forward to *now*, so patterns stay useful across days.

```bash
# 1) Record new history (from repo root)
cd GTFS-RT
python3 record_feed.py \
  https://trujillo-admin-storage.s3.us-east-1.amazonaws.com/driver/gtfsrt/pe-trujillo.proto \
  -o history/

# 2) Regenerate patterns
cd ../gtfs-rt-proxy/simulator
python3 analyze.py --history ../../GTFS-RT/history/ --out patterns.json

# 3) Commit & deploy
git add patterns.json
git commit -m "refresh simulator patterns"
git push
ssh root@trujillo.trufi.dev \
  "cd /root/gtfs-rt-proxy && git pull && docker compose up -d --build simulator"
```

## analyze.py — what it extracts

For each recorded `.proto`, groups observations by
`(licensePlate, startDate, startTime)` — one group per real bus run.

Per group it keeps:
- `route_id`, `direction_id` (most frequent across samples)
- `duration_seconds`
- A uniform sample of `(t, lat, lon, heading)` every N seconds (default 5)

Written to `patterns.json`:

```json
{
  "source": { "files_analyzed": 222, "span_utc": ["...", "..."], ... },
  "trajectories": [
    {
      "route_id": "19",
      "direction_id": 1,
      "duration_seconds": 425,
      "sample_plate": "DF-6767",
      "points": [
        { "t": 0,  "lat": -8.10471, "lon": -79.03387, "heading": 29.5 },
        { "t": 5,  "lat": -8.10423, "lon": -79.03351, "heading": 31.2 },
        ...
      ]
    }
  ]
}
```

**Trajectories store no absolute date/time** — only the relative offset `t`
from trajectory start. This is what lets the simulator replay any pattern
at today's date.

## server.py — runtime loop

On startup:
1. Loads `patterns.json`
2. Builds an in-memory pool: each recorded trajectory is cloned
   `CLONE_FACTOR` times (env, default 3) with a random synthetic license
   plate and a staggered start offset inside its duration (so clones are at
   different stages of the trip from the first tick)
3. Listens on `PORT` (env, default 9000)

On each `GET /pe-trujillo.proto`:
1. `now = datetime.utcnow()`
2. For every clone in the pool:
   - `elapsed = now - spawn`
   - `t_in_traj = elapsed % duration` (loop forever)
   - Linearly interpolate `(lat, lon, heading)` at `t_in_traj`
   - `start_date`, `start_time` are derived from `spawn + loop_iter * duration`
     → always today (or very recent)
3. Serializes a `FeedMessage` with one `VehiclePosition` entity per clone

## Endpoints

| Path | Response |
|---|---|
| `GET /pe-trujillo.proto` | Binary GTFS-RT feed |
| `GET /gtfsrt.proto` | Same |
| `GET /healthz` | JSON with pool stats |

## Environment variables

| Var | Default | Purpose |
|---|---|---|
| `PATTERNS_PATH` | `/app/patterns.json` | Path to patterns file inside the container |
| `CLONE_FACTOR` | `3` | Number of synthetic clones per real trajectory |
| `PORT` | `9000` | HTTP port |

## Toggle from the proxy side

The proxy (`gtfs-rt-proxy`) decides whether to hit S3 or this simulator
based on the `SIMULATED` env var in `.env`:

```bash
# Enable simulator as upstream
echo "SIMULATED=true" > .env
docker compose up -d proxy

# Back to production
echo "SIMULATED=false" > .env
docker compose up -d proxy
```

OTP doesn't need any config change — it keeps pulling from the proxy's
URL. Only the proxy's view of "upstream" changes.
