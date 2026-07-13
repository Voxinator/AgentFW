// auth.js — authentication helpers.
//
// NOTE: this module has grown organically. It currently holds password
// hashing, API token creation/validation, cookie parsing, and a couple of
// misc helpers. Candidate for a cleanup pass at some point.

'use strict';

const crypto = require('node:crypto');

// Secret used to sign API tokens. In production this comes from the
// environment; the fallback keeps local dev and tests working.
const TOKEN_SECRET = process.env.TOKEN_SECRET || 'dev-secret-change-me';

// Default API token lifetime: 1 hour.
const TOKEN_TTL_MS = 60 * 60 * 1000;

// ---------------------------------------------------------------------------
// Password hashing
// ---------------------------------------------------------------------------

function hashPassword(password, salt) {
  salt = salt || crypto.randomBytes(16).toString('hex');
  const hash = crypto
    .scryptSync(password, salt, 32)
    .toString('hex');
  return `${salt}:${hash}`;
}

function verifyPassword(password, stored) {
  const [salt, expected] = stored.split(':');
  const actual = crypto.scryptSync(password, salt, 32).toString('hex');
  return timingSafeEqual(actual, expected);
}

// ---------------------------------------------------------------------------
// API tokens (HMAC-signed, stateless)
//
// Format: base64url(payloadJson) + "." + base64url(hmacSha256(payload))
// ---------------------------------------------------------------------------

function createToken(payload, ttlMs) {
  const body = {
    ...payload,
    iat: Date.now(),
    exp: Date.now() + (ttlMs === undefined ? TOKEN_TTL_MS : ttlMs),
  };
  const encoded = Buffer.from(JSON.stringify(body)).toString('base64url');
  const sig = sign(encoded);
  return `${encoded}.${sig}`;
}

function verifyToken(token) {
  if (typeof token !== 'string') return null;
  const dot = token.lastIndexOf('.');
  if (dot === -1) return null;

  const encoded = token.slice(0, dot);
  const sig = token.slice(dot + 1);
  if (!timingSafeEqual(sign(encoded), sig)) return null; // invalid signature

  let body;
  try {
    body = JSON.parse(Buffer.from(encoded, 'base64url').toString('utf8'));
  } catch {
    return null; // malformed payload
  }
  if (typeof body.exp !== 'number' || body.exp < Date.now()) {
    return null; // expired token
  }
  return body;
}

function sign(data) {
  return crypto
    .createHmac('sha256', TOKEN_SECRET)
    .update(data)
    .digest('base64url');
}

function timingSafeEqual(a, b) {
  const ab = Buffer.from(String(a));
  const bb = Buffer.from(String(b));
  if (ab.length !== bb.length) return false;
  return crypto.timingSafeEqual(ab, bb);
}

// ---------------------------------------------------------------------------
// Cookie helpers (used by the session layer and the endpoints)
// ---------------------------------------------------------------------------

function parseCookies(header) {
  const out = {};
  if (!header) return out;
  for (const part of header.split(';')) {
    const eq = part.indexOf('=');
    if (eq === -1) continue;
    const name = part.slice(0, eq).trim();
    const value = part.slice(eq + 1).trim();
    if (name) out[name] = decodeURIComponent(value);
  }
  return out;
}

function sessionCookie(sessionId, maxAgeSeconds) {
  return `sid=${encodeURIComponent(sessionId)}; HttpOnly; Path=/; Max-Age=${maxAgeSeconds}; SameSite=Lax`;
}

function clearSessionCookie() {
  return 'sid=; HttpOnly; Path=/; Max-Age=0; SameSite=Lax';
}

// ---------------------------------------------------------------------------
// Misc
// ---------------------------------------------------------------------------

function bearerToken(req) {
  const header = req.headers['authorization'];
  if (!header || !header.startsWith('Bearer ')) return null;
  return header.slice('Bearer '.length).trim();
}

module.exports = {
  hashPassword,
  verifyPassword,
  createToken,
  verifyToken,
  parseCookies,
  sessionCookie,
  clearSessionCookie,
  bearerToken,
  TOKEN_TTL_MS,
};
