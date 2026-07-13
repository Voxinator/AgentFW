// server.js — HTTP server and routing.
//
// Auth model: a request is authenticated if it carries EITHER a valid `sid`
// session cookie (browser flow) OR a valid `Authorization: Bearer <token>`
// header (API flow). Each protected endpoint currently performs this check
// inline — see the repeated cookie/token blocks below.

'use strict';

const http = require('node:http');

const auth = require('./auth');
const sessions = require('./sessions');
const users = require('./users');
const orders = require('./orders');

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', (chunk) => {
      data += chunk;
      if (data.length > 64 * 1024) {
        reject(new Error('body too large'));
        req.destroy();
      }
    });
    req.on('end', () => resolve(data));
    req.on('error', reject);
  });
}

function json(res, status, payload) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(payload));
}

function createServer() {
  return http.createServer(async (req, res) => {
    const url = new URL(req.url, 'http://localhost');
    const route = `${req.method} ${url.pathname}`;

    try {
      switch (route) {
        case 'GET /health':
          return json(res, 200, { ok: true });

        case 'POST /login': {
          const body = await readBody(req);
          return users.handleLogin(req, res, body);
        }

        case 'POST /logout':
          return users.handleLogout(req, res);

        case 'GET /profile': {
          // -- auth check (session cookie, then bearer token) --------------
          let username = null;
          const cookies = auth.parseCookies(req.headers['cookie']);
          const session = sessions.getSession(cookies.sid);
          if (session) {
            username = session.username;
          } else {
            const token = auth.bearerToken(req);
            const claims = token ? auth.verifyToken(token) : null;
            if (claims) username = claims.sub;
          }
          if (!username) return json(res, 401, { error: 'unauthorized' });
          // -----------------------------------------------------------------
          const user = users.getUser(username);
          if (!user) return json(res, 401, { error: 'unauthorized' });
          return json(res, 200, { username, email: user.email, role: user.role });
        }

        case 'GET /orders': {
          // -- auth check (session cookie, then bearer token) --------------
          let username = null;
          const cookies = auth.parseCookies(req.headers['cookie']);
          const session = sessions.getSession(cookies.sid);
          if (session) {
            username = session.username;
          } else {
            const token = auth.bearerToken(req);
            const claims = token ? auth.verifyToken(token) : null;
            if (claims) username = claims.sub;
          }
          if (!username) return json(res, 401, { error: 'unauthorized' });
          // -----------------------------------------------------------------
          return json(res, 200, { orders: orders.ordersFor(username) });
        }

        case 'GET /admin': {
          // -- auth check (session cookie, then bearer token) --------------
          let username = null;
          const cookies = auth.parseCookies(req.headers['cookie']);
          const session = sessions.getSession(cookies.sid);
          if (session) {
            username = session.username;
          } else {
            const token = auth.bearerToken(req);
            const claims = token ? auth.verifyToken(token) : null;
            if (claims) username = claims.sub;
          }
          if (!username) return json(res, 401, { error: 'unauthorized' });
          // -----------------------------------------------------------------
          const user = users.getUser(username);
          if (!user || user.role !== 'admin') {
            return json(res, 403, { error: 'forbidden' });
          }
          return json(res, 200, { stats: { users: 2, sessionsSweptAt: null } });
        }

        default:
          return json(res, 404, { error: 'not found' });
      }
    } catch (err) {
      return json(res, 500, { error: 'internal error' });
    }
  });
}

module.exports = { createServer };

if (require.main === module) {
  const port = Number(process.env.PORT) || 3000;
  createServer().listen(port, () => {
    console.log(`listening on http://localhost:${port}`);
  });
}
