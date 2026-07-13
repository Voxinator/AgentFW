// users.js — user store plus the login/logout request handlers.

'use strict';

const auth = require('./auth');
const sessions = require('./sessions');

// Seed users. Passwords are scrypt-hashed at startup so nothing plaintext
// lives past module init.
const users = new Map([
  ['alice', { passwordHash: auth.hashPassword('correct horse battery'), role: 'user',  email: 'alice@example.com' }],
  ['bob',   { passwordHash: auth.hashPassword('hunter2hunter2'),        role: 'admin', email: 'bob@example.com' }],
]);

function getUser(username) {
  return users.get(username) || null;
}

function authenticate(username, password) {
  const user = users.get(username);
  if (!user) return null;
  if (!auth.verifyPassword(password, user.passwordHash)) return null;
  return { username, role: user.role, email: user.email };
}

// POST /login  { username, password }
// On success: sets the session cookie AND returns a bearer token for API use.
function handleLogin(req, res, body) {
  let creds;
  try {
    creds = JSON.parse(body || '{}');
  } catch {
    res.writeHead(400, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'invalid JSON body' }));
    return;
  }

  const user = authenticate(creds.username, creds.password || '');
  if (!user) {
    res.writeHead(401, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'invalid credentials' }));
    return;
  }

  const sessionId = sessions.createSession(user.username);
  const token = auth.createToken({ sub: user.username, role: user.role });

  res.writeHead(200, {
    'Content-Type': 'application/json',
    'Set-Cookie': auth.sessionCookie(sessionId, sessions.SESSION_TTL_MS / 1000),
  });
  res.end(JSON.stringify({ ok: true, username: user.username, token }));
}

// POST /logout — destroys the cookie session if present.
function handleLogout(req, res) {
  const cookies = auth.parseCookies(req.headers['cookie']);
  if (cookies.sid) sessions.destroySession(cookies.sid);
  res.writeHead(200, {
    'Content-Type': 'application/json',
    'Set-Cookie': auth.clearSessionCookie(),
  });
  res.end(JSON.stringify({ ok: true }));
}

module.exports = { getUser, authenticate, handleLogin, handleLogout };
