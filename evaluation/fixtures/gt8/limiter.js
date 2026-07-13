'use strict';

// Simple fixed-window per-IP rate limiter middleware for Express.
// No external dependencies; counters live in process memory.

const MAX_REQS = 100; // requests allowed per window per client IP
const WINDOW_MS = 60 * 1000; // 1 minute window

const windows = new Map(); // ip -> { count, windowStart }

function clientKey(req) {
  return req.ip || req.connection.remoteAddress || 'unknown';
}

function rateLimiter(req, res, next) {
  const key = clientKey(req);
  const now = Date.now();
  let entry = windows.get(key);

  if (!entry || now - entry.windowStart >= WINDOW_MS) {
    entry = { count: 0, windowStart: now };
    windows.set(key, entry);
  }

  entry.count += 1;

  const remaining = Math.max(0, MAX_REQS - entry.count);
  res.setHeader('X-RateLimit-Limit', String(MAX_REQS));
  res.setHeader('X-RateLimit-Remaining', String(remaining));

  if (entry.count > MAX_REQS) {
    const retryAfterSec = Math.ceil((entry.windowStart + WINDOW_MS - now) / 1000);
    res.setHeader('Retry-After', String(retryAfterSec));
    res.status(429).json({ error: 'Too many requests' });
    return;
  }

  next();
}

// Periodically drop stale windows so the map does not grow unbounded.
setInterval(() => {
  const now = Date.now();
  for (const [key, entry] of windows) {
    if (now - entry.windowStart >= WINDOW_MS) {
      windows.delete(key);
    }
  }
}, WINDOW_MS).unref();

module.exports = { rateLimiter, MAX_REQS, WINDOW_MS };
