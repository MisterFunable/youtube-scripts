// Paste this file into an n8n Function node, or copy the functions you need.
// Assumes incoming items are one video per item (YouTube node output). Returns a single item summarizing insights.

function safeInt(value, def = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? Math.trunc(n) : def;
}

function parseIsoDate(s) {
  try {
    if (!s) return null;
    const d = new Date(s);
    if (Number.isNaN(d.getTime())) return null;
    return d;
  } catch {
    return null;
  }
}

function median(arr) {
  if (!arr.length) return 0;
  const s = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

function parseISODuration(iso) {
  // Parses ISO 8601 duration like PT1H2M3S to seconds
  if (!iso || typeof iso !== 'string') return 0;
  const re = /P(?:([0-9]+)Y)?(?:([0-9]+)M)?(?:([0-9]+)W)?(?:([0-9]+)D)?(?:T(?:([0-9]+)H)?(?:([0-9]+)M)?(?:([0-9]+)S)?)?/;
  const m = iso.match(re);
  if (!m) return 0;
  const years = Number(m[1] || 0);
  const months = Number(m[2] || 0);
  const weeks = Number(m[3] || 0);
  const days = Number(m[4] || 0);
  const hours = Number(m[5] || 0);
  const minutes = Number(m[6] || 0);
  const seconds = Number(m[7] || 0);
  const totalDays = years * 365 + months * 30 + weeks * 7 + days;
  return totalDays * 86400 + hours * 3600 + minutes * 60 + seconds;
}

function normalizeVideo(raw) {
  // Accepts Search results, Videos results, or shapes with a nested `resource`
  const base = raw.resource || raw;
  const snippet = base.snippet || raw.snippet || {};

  // Resolve id
  let id = base.id ?? raw.id ?? base.videoId ?? raw.videoId;
  if (id && typeof id === 'object' && id.videoId) id = id.videoId;
  id = String(id || '');

  const title = String(snippet.title || base.title || raw.title || '');
  const publishedAt = String(
    snippet.publishedAt || snippet.publishTime || base.publishedAt || raw.publishedAt || ''
  );

  // Duration
  let durationSeconds = 0;
  const contentDetails = base.contentDetails || raw.contentDetails || {};
  if (typeof base.duration_seconds !== 'undefined') {
    durationSeconds = safeInt(base.duration_seconds, 0);
  } else if (typeof raw.duration_seconds !== 'undefined') {
    durationSeconds = safeInt(raw.duration_seconds, 0);
  } else if (contentDetails.duration) {
    durationSeconds = safeInt(parseISODuration(contentDetails.duration), 0);
  }

  // Statistics
  const statistics = base.statistics || raw.statistics || {};
  const viewCount = safeInt(
    typeof statistics.viewCount !== 'undefined' ? statistics.viewCount : (base.viewCount ?? raw.viewCount),
    0
  );
  const likeCount = safeInt(
    typeof statistics.likeCount !== 'undefined' ? statistics.likeCount : (base.likeCount ?? raw.likeCount),
    0
  );
  const commentCount = safeInt(
    typeof statistics.commentCount !== 'undefined' ? statistics.commentCount : (base.commentCount ?? raw.commentCount),
    0
  );

  return {
    id,
    title,
    publishedAt,
    duration_seconds: durationSeconds,
    viewCount,
    likeCount,
    commentCount,
  };
}

function computeViewsPerDay(v) {
  const now = new Date();
  const dt = parseIsoDate(v.publishedAt);
  const days = Math.max(1, Math.floor((now - dt) / (1000 * 60 * 60 * 24)));
  const views = safeInt(v.viewCount, 0);
  return views / days;
}

function applyFilters(videos, varsConfig) {
  const excludeCfg = (varsConfig.exclude || {});
  const filtersCfg = (varsConfig.filters || {});

  const excludedIds = new Set(excludeCfg.videoIds || []);
  const titleContains = (excludeCfg.titleContains || []).map(s => String(s).toLowerCase());
  const titleRegex = excludeCfg.titleRegex ? new RegExp(excludeCfg.titleRegex, 'i') : null;
  const excludeShorts = excludeCfg.excludeShorts !== false;
  const maxShortSeconds = safeInt(excludeCfg.maxDurationSecondsForShorts, 60);

  const minViews = safeInt(filtersCfg.minViews, 0);
  const minDuration = safeInt(filtersCfg.minDurationSeconds, 0);
  const start = filtersCfg.dateRange?.start ? parseIsoDate(filtersCfg.dateRange.start) : null;
  const end = filtersCfg.dateRange?.end ? parseIsoDate(filtersCfg.dateRange.end) : null;

  const stats = { inputCount: videos.length, excludedCount: 0, filteredCount: 0 };
  const out = [];

  for (const v of videos) {
    const id = String(v.id || '');
    const title = String(v.title || '');
    const dur = safeInt(v.duration_seconds, 0);
    const views = safeInt(v.viewCount, 0);
    const published = parseIsoDate(v.publishedAt);

    if (excludedIds.has(id)) { stats.excludedCount++; continue; }
    const tl = title.toLowerCase();
    if (titleContains.some(t => tl.includes(t))) { stats.excludedCount++; continue; }
    if (titleRegex && titleRegex.test(title)) { stats.excludedCount++; continue; }
    if (excludeShorts && dur > 0 && dur <= maxShortSeconds) { stats.excludedCount++; continue; }

    if (dur < minDuration) { stats.filteredCount++; continue; }
    if (views < minViews) { stats.filteredCount++; continue; }
    if ((start && published < start) || (end && published > end)) { stats.filteredCount++; continue; }

    out.push(v);
  }

  return { filtered: out, stats };
}

function publishTimeInsights(videos, metric) {
  const byDow = Array.from({ length: 7 }, () => []);
  const byHour = Array.from({ length: 24 }, () => []);

  const getMetric = (v) => {
    if (metric === 'viewsPerDay') return computeViewsPerDay(v);
    return safeInt(v[metric], 0);
  };

  for (const v of videos) {
    const dt = parseIsoDate(v.publishedAt);
    if (!dt) continue;
    const value = getMetric(v);
    byDow[dt.getDay() === 0 ? 6 : dt.getDay() - 1].push(value); // Normalize Monday=0
    byHour[dt.getHours()].push(value);
  }

  const summarize = (groups) => {
    const out = {};
    groups.forEach((arr, idx) => {
      if (!arr.length) out[String(idx)] = { avg: 0, median: 0, count: 0 };
      else out[String(idx)] = {
        avg: Math.round((arr.reduce((a, b) => a + b, 0) / arr.length) * 100) / 100,
        median: Math.round(median(arr) * 100) / 100,
        count: arr.length,
      };
    });
    return out;
  };

  const combos = new Map(); // key: `${dow}-${hr}` -> values
  const addCombo = (dow, hr, val) => {
    const key = `${dow}-${hr}`;
    const arr = combos.get(key) || [];
    arr.push(val);
    combos.set(key, arr);
  };

  for (const v of videos) {
    const dt = parseIsoDate(v.publishedAt);
    if (!dt) continue;
    const dow = dt.getDay() === 0 ? 6 : dt.getDay() - 1; // Monday=0
    const hr = dt.getHours();
    addCombo(dow, hr, getMetric(v));
  }

  const bestCombos = Array.from(combos.entries()).map(([key, arr]) => {
    const [dow, hr] = key.split('-').map(Number);
    const avg = arr.reduce((a, b) => a + b, 0) / arr.length;
    return { dayOfWeek: dow, hourOfDay: hr, avg: Math.round(avg * 100) / 100, count: arr.length };
  }).sort((a, b) => (b.avg - a.avg) || (b.count - a.count)).slice(0, 10);

  return {
    byDayOfWeek: summarize(byDow),
    byHourOfDay: summarize(byHour),
    bestDayHourCombos: bestCombos,
  };
}

function popularityOverTime(videos, metric, period) {
  const buckets = new Map();
  const getMetric = (v) => metric === 'viewsPerDay' ? computeViewsPerDay(v) : safeInt(v[metric], 0);

  for (const v of videos) {
    const dt = parseIsoDate(v.publishedAt);
    if (!dt) continue;
    const key = period === 'week'
      ? `${dt.getUTCFullYear()}-W${String(getISOWeek(dt)).padStart(2, '0')}`
      : `${dt.getUTCFullYear()}-${String(dt.getUTCMonth() + 1).padStart(2, '0')}`;
    const arr = buckets.get(key) || [];
    arr.push(getMetric(v));
    buckets.set(key, arr);
  }

  const result = Array.from(buckets.entries()).sort(([a], [b]) => a.localeCompare(b)).map(([periodKey, arr]) => {
    const sum = arr.reduce((a, b) => a + b, 0);
    return {
      period: periodKey,
      count: arr.length,
      sum: Math.round(sum * 100) / 100,
      avg: Math.round((sum / arr.length) * 100) / 100,
      median: Math.round(median(arr) * 100) / 100,
    };
  });

  return result;
}

function getISOWeek(date) {
  // ISO week-numbering year algorithm
  const tmp = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
  // Thursday in current week decides the year
  tmp.setUTCDate(tmp.getUTCDate() + 4 - (tmp.getUTCDay() || 7));
  const yearStart = new Date(Date.UTC(tmp.getUTCFullYear(), 0, 1));
  const weekNo = Math.ceil((((tmp - yearStart) / 86400000) + 1) / 7);
  return weekNo;
}

function computeTopVideos(videos, metric, limit, normalizeByDuration) {
  const getMetric = (v) => metric === 'viewsPerDay' ? computeViewsPerDay(v) : safeInt(v[metric], 0);
  const arr = videos.map(v => {
    let val = getMetric(v);
    if (normalizeByDuration) {
      const dur = Math.max(1, safeInt(v.duration_seconds, 0));
      val = val / dur;
    }
    return { ...v, _metricValue: val };
  }).sort((a, b) => b._metricValue - a._metricValue).slice(0, limit);

  return arr.map(e => ({
    id: e.id,
    title: e.title,
    publishedAt: e.publishedAt,
    duration_seconds: safeInt(e.duration_seconds, 0),
    [metric]: metric === 'viewsPerDay' ? Math.round(e._metricValue * 100) / 100 : safeInt(e[metric], 0),
    _metricValue: Math.round(e._metricValue * 100) / 100,
  }));
}

// n8n Function Node entry
// Inputs: items[] where each item.json is a video object. Optionally pass a vars object via the first item: items[0].json.vars
// Output: one item with insights
const varsConfig = (items[0] && items[0].json && items[0].json.vars) || {
  exclude: { excludeShorts: true, maxDurationSecondsForShorts: 60 },
  filters: { minViews: 0, minDurationSeconds: 0, dateRange: { start: null, end: null } },
  insights: { metric: 'viewCount', topVideosLimit: 10, normalizeByDuration: false, popularityPeriod: 'month' },
};

const metric = String(varsConfig.insights?.metric || 'viewCount');
const topLimit = Number(varsConfig.insights?.topVideosLimit || 10);
const normalizeByDuration = Boolean(varsConfig.insights?.normalizeByDuration || false);
const popularityPeriod = String(varsConfig.insights?.popularityPeriod || 'month');

const videos = items
  .map(i => normalizeVideo(i.json))
  .filter(v => v.id); // drop non-video items (e.g., config-only)
const { filtered, stats } = applyFilters(videos, varsConfig);

const topVideos = computeTopVideos(filtered, metric, topLimit, normalizeByDuration);
const timeInsights = publishTimeInsights(filtered, metric);
const popularity = popularityOverTime(filtered, metric, popularityPeriod);

return [{ json: { stats, metric, topVideos, publishTimeInsights: timeInsights, popularityOverTime: popularity } }];


