# orderdesk

A small order-lookup service with username/password login. Zero runtime
dependencies — everything is built on Node's standard library (`node:http`,
`node:crypto`, `node:test`).

## Running

```sh
node src/server.js          # listens on PORT (default 3000)
```

## Tests

```sh
./run-tests.sh              # or: node --test "tests/**/*.test.js"
```

## API

| Route          | Auth      | Description                                  |
|----------------|-----------|----------------------------------------------|
| `POST /login`  | none      | JSON `{username, password}`; sets a `sid` session cookie and returns a bearer token |
| `POST /logout` | none      | destroys the current cookie session          |
| `GET /profile` | required  | current user's profile                       |
| `GET /orders`  | required  | current user's orders                        |
| `GET /admin`   | admin     | service stats                                |
| `GET /health`  | none      | liveness probe                               |

Authenticated routes accept **either** a `sid` session cookie (browser flow)
**or** an `Authorization: Bearer <token>` header (API flow). Tokens are
HMAC-SHA256 signed and expire after 1 hour; cookie sessions are stored
server-side in memory and expire after 30 minutes.

Seed users (dev only): `alice` / `correct horse battery` (user),
`bob` / `hunter2hunter2` (admin).

Set `TOKEN_SECRET` in production; the checked-in default is for local
development only.
