'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { createServer } = require('../src/server');
const auth = require('../src/auth');
const sessions = require('../src/sessions');

let server;
let base;

test.before(async () => {
  server = createServer();
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  base = `http://127.0.0.1:${server.address().port}`;
});

test.after(async () => {
  await new Promise((resolve) => server.close(resolve));
});

async function login(username, password) {
  const res = await fetch(`${base}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  return res;
}

test('login succeeds with valid credentials and issues a session + token', async () => {
  const res = await login('alice', 'correct horse battery');
  assert.equal(res.status, 200);

  const setCookie = res.headers.get('set-cookie');
  assert.ok(setCookie && setCookie.includes('sid='), 'sets a sid session cookie');

  const body = await res.json();
  assert.equal(body.username, 'alice');
  assert.ok(body.token, 'returns a bearer token');
});

test('authenticated request via session cookie returns profile', async () => {
  const res = await login('alice', 'correct horse battery');
  const cookie = res.headers.get('set-cookie').split(';')[0];

  const profile = await fetch(`${base}/profile`, { headers: { Cookie: cookie } });
  assert.equal(profile.status, 200);
  const body = await profile.json();
  assert.equal(body.email, 'alice@example.com');
});

test('authenticated request via bearer token returns orders', async () => {
  const res = await login('alice', 'correct horse battery');
  const { token } = await res.json();

  const ordersRes = await fetch(`${base}/orders`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  assert.equal(ordersRes.status, 200);
  const body = await ordersRes.json();
  assert.ok(Array.isArray(body.orders) && body.orders.length > 0);
});

test('login with wrong password is rejected with 401', async () => {
  const res = await login('alice', 'wrong-password');
  assert.equal(res.status, 401);
  const body = await res.json();
  assert.match(body.error, /invalid/);
});

test('request with no credentials is rejected with 401', async () => {
  const res = await fetch(`${base}/profile`);
  assert.equal(res.status, 401);
});

test('request with an invalid (tampered) token is rejected with 401', async () => {
  const res = await login('alice', 'correct horse battery');
  const { token } = await res.json();
  const tampered = token.slice(0, -4) + 'AAAA'; // corrupt the signature

  const profile = await fetch(`${base}/profile`, {
    headers: { Authorization: `Bearer ${tampered}` },
  });
  assert.equal(profile.status, 401);
});

test('request with garbage token is rejected with 401', async () => {
  const res = await fetch(`${base}/orders`, {
    headers: { Authorization: 'Bearer not-a-real-token' },
  });
  assert.equal(res.status, 401);
});

test('request with an expired token is rejected with 401', async () => {
  // Mint a token that expired 1s ago.
  const expired = auth.createToken({ sub: 'alice', role: 'user' }, -1000);
  assert.equal(auth.verifyToken(expired), null, 'expired token fails verification');

  const res = await fetch(`${base}/profile`, {
    headers: { Authorization: `Bearer ${expired}` },
  });
  assert.equal(res.status, 401);
});

test('request with an expired session cookie is rejected with 401', async () => {
  const res = await login('bob', 'hunter2hunter2');
  const cookie = res.headers.get('set-cookie').split(';')[0];
  const sid = decodeURIComponent(cookie.split('=')[1]);

  sessions.expireSession(sid);

  const profile = await fetch(`${base}/profile`, { headers: { Cookie: cookie } });
  assert.equal(profile.status, 401);
});

test('logout destroys the session; subsequent request is 401', async () => {
  const res = await login('alice', 'correct horse battery');
  const cookie = res.headers.get('set-cookie').split(';')[0];

  const out = await fetch(`${base}/logout`, {
    method: 'POST',
    headers: { Cookie: cookie },
  });
  assert.equal(out.status, 200);

  const profile = await fetch(`${base}/profile`, { headers: { Cookie: cookie } });
  assert.equal(profile.status, 401);
});

test('admin endpoint enforces role', async () => {
  const aliceRes = await login('alice', 'correct horse battery');
  const aliceCookie = aliceRes.headers.get('set-cookie').split(';')[0];
  const denied = await fetch(`${base}/admin`, { headers: { Cookie: aliceCookie } });
  assert.equal(denied.status, 403);

  const bobRes = await login('bob', 'hunter2hunter2');
  const bobCookie = bobRes.headers.get('set-cookie').split(';')[0];
  const allowed = await fetch(`${base}/admin`, { headers: { Cookie: bobCookie } });
  assert.equal(allowed.status, 200);
});
