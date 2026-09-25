from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import statistics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

data_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "q-vercel-latency.json"
)

with open(data_path, "r") as f:
    data = json.load(f)


class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float


def percentile_95(values):
    values = sorted(values)

    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * 0.95
    lower = int(position)
    upper = lower + 1

    if upper >= len(values):
        return values[lower]

    fraction = position - lower

    return values[lower] + (
        values[upper] - values[lower]
    ) * fraction


@app.post("/")
def analytics(request: AnalyticsRequest):

    result = {}

    for region in request.regions:

        records = [
            row for row in data
            if row["region"] == region
        ]

        latencies = [
            row["latency_ms"]
            for row in records
        ]

        uptimes = [
            row["uptime_pct"]
            for row in records
        ]

        result[region] = {
            "avg_latency": statistics.mean(latencies),
            "p95_latency": percentile_95(latencies),
            "avg_uptime": statistics.mean(uptimes),
            "breaches": sum(
                latency > request.threshold_ms
                for latency in latencies
            )
        }

    return result
