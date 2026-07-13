// sessions.js — in-memory, cookie-backed session store.
//
// A successful login creates a server-side session; the session id is handed
// to the browser in an HttpOnly `sid` cookie. Every authenticated request
// looks the id back up here.

'use strict';

const crypto = require('node:crypto');

const SESSION_TTL_MS = 30 * 60 * 1000; // 30 minutes

const store = new Map(); // sessionId -> { username, createdAt, expiresAt }

function createSession(username) {
  const id = crypto.randomBytes(24).toString('base64url');
  const now = Date.now();
  store.set(id, { username, createdAt: now, expiresAt: now + SESSION_TTL_MS });
  return id;
}

function getSession(id) {
  if (!id) return null;
  const session = store.get(id);
  if (!session) return null;
  if (session.expiresAt < Date.now()) {
    store.delete(id); // expired session — evict lazily
    return null;
  }
  return session;
}

function destroySession(id) {
  return store.delete(id);
}

// Periodic sweep so long-running processes don't leak expired entries.
function sweep() {
  const now = Date.now();
  for (const [id, session] of store) {
    if (session.expiresAt < now) store.delete(id);
  }
}

// Test/ops hook: force a session to be already expired.
function expireSession(id) {
  const session = store.get(id);
  if (session) session.expiresAt = Date.now() - 1;
}

module.exports = {
  createSession,
  getSession,
  destroySession,
  expireSession,
  sweep,
  SESSION_TTL_MS,
};
