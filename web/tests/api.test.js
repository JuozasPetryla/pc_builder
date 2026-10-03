import { afterEach, test } from "node:test";
import assert from "node:assert/strict";

const storage = new Map();
globalThis.sessionStorage = {
  getItem: (key) => storage.get(key),
  setItem: (key, value) => storage.set(key, value),
  removeItem: (key) => storage.delete(key),
};
globalThis.window = new EventTarget();
const { api, setSession, hasSession, refreshSession } =
  await import("../src/api.js");
const originalFetch = globalThis.fetch;
const pair = { access_token: "old-access", refresh_token: "old-refresh" };
const nextPair = { access_token: "new-access", refresh_token: "new-refresh" };
const response = (status, data) => ({
  status,
  ok: status < 400,
  json: async () => data,
});
afterEach(() => {
  setSession(null);
  globalThis.fetch = originalFetch;
});

test("concurrent 401 responses rotate once and retry with the new access token", async () => {
  setSession(pair);
  let refreshes = 0;
  globalThis.fetch = async (url, options) => {
    if (url.endsWith("/auth/refresh")) {
      refreshes++;
      assert.deepEqual(JSON.parse(options.body), {
        refresh_token: pair.refresh_token,
      });
      await new Promise((resolve) => setTimeout(resolve, 10));
      return response(200, nextPair);
    }
    return options.headers.Authorization === "Bearer new-access"
      ? response(200, { id: 1 })
      : response(401, { detail: "Expired" });
  };
  assert.deepEqual(await Promise.all([api("/builds"), api("/auth/me")]), [
    { id: 1 },
    { id: 1 },
  ]);
  assert.equal(refreshes, 1);
  assert.deepEqual(JSON.parse(storage.get("pc-builder-session")), nextPair);
});

test("revoked refresh clears the session and emits expiration", async () => {
  setSession(pair);
  let expired = false;
  window.addEventListener(
    "session-expired",
    () => {
      expired = true;
    },
    { once: true },
  );
  globalThis.fetch = async () => response(401, { detail: "Expired" });
  await assert.rejects(api("/builds"), /Expired/);
  assert.equal(hasSession(), false);
  assert.equal(expired, true);
});

test("failed login does not try refresh and 204 responses do not parse JSON", async () => {
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    return response(401, { detail: "Wrong password" });
  };
  await assert.rejects(api("/auth/login", "POST", {}, false), /Wrong password/);
  assert.equal(calls, 1);
  globalThis.fetch = async () => ({
    status: 204,
    ok: true,
    json: () => {
      throw new Error("Unexpected JSON parsing");
    },
  });
  assert.equal(await api("/builds/1", "DELETE"), null);
});

test("network failure preserves refresh token and validation errors name the field", async () => {
  setSession(pair);
  globalThis.fetch = async () => {
    throw new TypeError("Network failed");
  };
  await assert.rejects(refreshSession(), /Nepavyko pasiekti serverio/);
  assert.equal(hasSession(), true);
  globalThis.fetch = async () =>
    response(422, { detail: [{ loc: ["body", "name"], msg: "Too short" }] });
  await assert.rejects(api("/builds", "POST", {}), /name: Too short/);
});

test("an in-flight refresh cannot resurrect a cleared session", async () => {
  setSession(pair);
  let finish;
  globalThis.fetch = () =>
    new Promise((resolve) => {
      finish = resolve;
    });
  const request = refreshSession();
  await Promise.resolve();
  setSession(null);
  finish(response(200, nextPair));
  await assert.rejects(request, /Sesija pasikeitė/);
  assert.equal(hasSession(), false);
});

test("refresh without a session can be retried after login", async () => {
  setSession(null);
  await assert.rejects(refreshSession(), /Prisijunkite/);
  setSession(pair);
  globalThis.fetch = async () => response(200, nextPair);
  assert.deepEqual(await refreshSession(), nextPair);
});
