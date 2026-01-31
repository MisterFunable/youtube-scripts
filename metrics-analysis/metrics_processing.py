from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _parse_iso_datetime(dt: str) -> datetime:
    # Accepts variants like 2024-01-02T03:04:05Z or 2024-01-02
    try:
        if dt.endswith("Z"):
            return datetime.fromisoformat(dt.replace("Z", "+00:00"))
        if len(dt) == 10:
            return datetime.fromisoformat(dt)
        return datetime.fromisoformat(dt)
    except Exception:
        # Fallback to naive parsing of date only
        return datetime.fromisoformat(dt[:10])


def _median(values: List[float]) -> float:
    n = len(values)
    if n == 0:
        return 0.0
    s = sorted(values)
    mid = n // 2
    if n % 2 == 1:
        return float(s[mid])
    return (s[mid - 1] + s[mid]) / 2.0


def apply_filters(
    videos: List[Dict[str, Any]],
    vars_config: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Apply exclusion rules and filters from vars_config to the list of videos.

    Expected video shape (keys used):
      - id, title, publishedAt (ISO string)
      - duration_seconds, viewCount, likeCount, commentCount
    """
    exclude_cfg = (vars_config.get("exclude") or {})
    filters_cfg = (vars_config.get("filters") or {})

    excluded_ids = set(exclude_cfg.get("videoIds") or [])
    title_contains = [t.lower() for t in (exclude_cfg.get("titleContains") or [])]
    title_regex: Optional[str] = exclude_cfg.get("titleRegex") or None
    exclude_shorts = bool(exclude_cfg.get("excludeShorts", True))
    max_short_seconds = int(exclude_cfg.get("maxDurationSecondsForShorts", 60))

    import re
    title_re = re.compile(title_regex, re.IGNORECASE) if title_regex else None

    min_views = _safe_int(filters_cfg.get("minViews"), 0)
    min_duration = _safe_int(filters_cfg.get("minDurationSeconds"), 0)

    date_range = filters_cfg.get("dateRange") or {}
    start_date = date_range.get("start")
    end_date = date_range.get("end")
    start_dt = _parse_iso_datetime(start_date) if start_date else None
    end_dt = _parse_iso_datetime(end_date) if end_date else None

    filtered: List[Dict[str, Any]] = []
    stats = {
        "inputCount": len(videos),
        "excludedCount": 0,
        "filteredCount": 0,
    }

    for v in videos:
        vid = str(v.get("id", ""))
        title = str(v.get("title", ""))
        duration = _safe_int(v.get("duration_seconds"), 0)
        views = _safe_int(v.get("viewCount"), 0)
        published = str(v.get("publishedAt", ""))

        # Exclusions
        if vid in excluded_ids:
            stats["excludedCount"] += 1
            continue
        tl = title.lower()
        if any(term in tl for term in title_contains):
            stats["excludedCount"] += 1
            continue
        if title_re and title_re.search(title):
            stats["excludedCount"] += 1
            continue
        if exclude_shorts and duration > 0 and duration <= max_short_seconds:
            stats["excludedCount"] += 1
            continue

        # Filters
        if duration < min_duration:
            stats["filteredCount"] += 1
            continue
        if views < min_views:
            stats["filteredCount"] += 1
            continue
        if start_dt or end_dt:
            try:
                pdt = _parse_iso_datetime(published)
                if start_dt and pdt < start_dt:
                    stats["filteredCount"] += 1
                    continue
                if end_dt and pdt > end_dt:
                    stats["filteredCount"] += 1
                    continue
            except Exception:
                # If we cannot parse the date, exclude from analysis
                stats["filteredCount"] += 1
                continue

        filtered.append(v)

    return filtered, stats


def compute_views_per_day(v: Dict[str, Any], now: Optional[datetime] = None) -> float:
    now = now or datetime.now(timezone.utc)
    published = str(v.get("publishedAt", ""))
    try:
        pdt = _parse_iso_datetime(published)
        if pdt.tzinfo is None:
            pdt = pdt.replace(tzinfo=timezone.utc)
        delta_days = max(1, (now - pdt).days)
    except Exception:
        delta_days = 1
    views = _safe_int(v.get("viewCount"), 0)
    return float(views) / float(delta_days)


def compute_top_videos(
    videos: List[Dict[str, Any]],
    metric: str = "viewCount",
    limit: int = 10,
    normalize_by_duration: bool = False,
) -> List[Dict[str, Any]]:
    valid_metrics = {"viewCount", "likeCount", "commentCount", "duration_seconds", "viewsPerDay"}
    if metric not in valid_metrics:
        metric = "viewCount"

    def metric_value(v: Dict[str, Any]) -> float:
        if metric == "viewsPerDay":
            value = compute_views_per_day(v)
        else:
            value = float(_safe_int(v.get(metric), 0))
        if normalize_by_duration:
            duration = max(1, _safe_int(v.get("duration_seconds"), 0))
            return value / float(duration)
        return value

    enriched = []
    for v in videos:
        mv = metric_value(v)
        enriched.append({
            **v,
            "_metricValue": mv,
        })

    enriched.sort(key=lambda x: x["_metricValue"], reverse=True)
    return [
        {
            "id": e.get("id"),
            "title": e.get("title"),
            "publishedAt": e.get("publishedAt"),
            metric: _safe_int(e.get(metric), 0) if metric != "viewsPerDay" else round(e.get("_metricValue", 0.0), 2),
            "duration_seconds": _safe_int(e.get("duration_seconds"), 0),
            "_metricValue": round(e.get("_metricValue", 0.0), 2),
        }
        for e in enriched[:limit]
    ]


def publish_time_insights(
    videos: List[Dict[str, Any]],
    metric: str = "viewCount",
) -> Dict[str, Any]:
    # Build arrays by day-of-week and hour-of-day
    by_dow: Dict[int, List[float]] = {i: [] for i in range(7)}  # Monday=0
    by_hour: Dict[int, List[float]] = {i: [] for i in range(24)}

    def get_metric(v: Dict[str, Any]) -> float:
        if metric == "viewsPerDay":
            return compute_views_per_day(v)
        return float(_safe_int(v.get(metric), 0))

    for v in videos:
        published = str(v.get("publishedAt", ""))
        try:
            dt = _parse_iso_datetime(published)
        except Exception:
            continue
        value = get_metric(v)
        by_dow[dt.weekday()].append(value)
        by_hour[dt.hour].append(value)

    def summarize(group: Dict[int, List[float]]) -> Dict[str, Dict[str, float]]:
        summary: Dict[str, Dict[str, float]] = {}
        for k, arr in group.items():
            if not arr:
                summary[str(k)] = {"avg": 0.0, "median": 0.0, "count": 0}
            else:
                avg = float(sum(arr)) / float(len(arr))
                med = _median(arr)
                summary[str(k)] = {"avg": round(avg, 2), "median": round(med, 2), "count": len(arr)}
        return summary

    by_dow_summary = summarize(by_dow)
    by_hour_summary = summarize(by_hour)

    # Identify top day-hour pairs by average metric
    combo_scores: List[Tuple[int, int, float]] = []
    for v in videos:
        published = str(v.get("publishedAt", ""))
        try:
            dt = _parse_iso_datetime(published)
        except Exception:
            continue
        combo_scores.append((dt.weekday(), dt.hour, get_metric(v)))

    # Aggregate by (dow, hour)
    from collections import defaultdict
    combo_map: Dict[Tuple[int, int], List[float]] = defaultdict(list)
    for dow, hr, val in combo_scores:
        combo_map[(dow, hr)].append(val)

    best_combos: List[Dict[str, Any]] = []
    for (dow, hr), arr in combo_map.items():
        if not arr:
            continue
        avg = float(sum(arr)) / float(len(arr))
        best_combos.append({
            "dayOfWeek": dow,  # Monday=0
            "hourOfDay": hr,
            "avg": round(avg, 2),
            "count": len(arr),
        })

    best_combos.sort(key=lambda x: (x["avg"], x["count"]), reverse=True)

    return {
        "byDayOfWeek": by_dow_summary,
        "byHourOfDay": by_hour_summary,
        "bestDayHourCombos": best_combos[:10],
    }


def popularity_over_time(
    videos: List[Dict[str, Any]],
    metric: str = "viewCount",
    period: str = "month",  # "month" or "week"
) -> List[Dict[str, Any]]:
    # Bucket videos by period of publish
    from collections import defaultdict
    buckets: Dict[str, List[float]] = defaultdict(list)

    def get_metric(v: Dict[str, Any]) -> float:
        if metric == "viewsPerDay":
            return compute_views_per_day(v)
        return float(_safe_int(v.get(metric), 0))

    for v in videos:
        published = str(v.get("publishedAt", ""))
        try:
            dt = _parse_iso_datetime(published)
        except Exception:
            continue
        if period == "week":
            iso_year, iso_week, _ = dt.isocalendar()
            key = f"{iso_year}-W{iso_week:02d}"
        else:
            key = dt.strftime("%Y-%m")
        buckets[key].append(get_metric(v))

    result: List[Dict[str, Any]] = []
    for key in sorted(buckets.keys()):
        arr = buckets[key]
        if not arr:
            continue
        result.append({
            "period": key,
            "count": len(arr),
            "sum": round(float(sum(arr)), 2),
            "avg": round(float(sum(arr)) / float(len(arr)), 2),
            "median": round(_median(arr), 2),
        })

    return result


def compute_insights(
    videos: List[Dict[str, Any]],
    vars_config: Dict[str, Any],
) -> Dict[str, Any]:
    insights_cfg = (vars_config.get("insights") or {})
    metric = str(insights_cfg.get("metric", "viewCount"))
    top_limit = int(insights_cfg.get("topVideosLimit", 10))
    norm_by_duration = bool(insights_cfg.get("normalizeByDuration", False))
    popularity_period = str(insights_cfg.get("popularityPeriod", "month"))

    filtered, stats = apply_filters(videos, vars_config)

    top_videos = compute_top_videos(
        filtered,
        metric=metric,
        limit=top_limit,
        normalize_by_duration=norm_by_duration,
    )

    time_insights = publish_time_insights(filtered, metric=metric)
    popularity = popularity_over_time(filtered, metric=metric, period=popularity_period)

    return {
        "stats": stats,
        "metric": metric,
        "topVideos": top_videos,
        "publishTimeInsights": time_insights,
        "popularityOverTime": popularity,
    }


if __name__ == "__main__":
    import json
    import os

    data_file = os.environ.get("VIDEO_LIST", "video_list.json")
    vars_file = os.environ.get("VARS_FILE", "vars.example.json")

    if not os.path.exists(data_file):
        raise SystemExit(f"Missing {data_file}. Provide a JSON array of videos.")
    with open(data_file, "r", encoding="utf-8") as f:
        videos = json.load(f)

    with open(vars_file, "r", encoding="utf-8") as f:
        vars_config = json.load(f)

    result = compute_insights(videos, vars_config)
    print(json.dumps(result, indent=2))


