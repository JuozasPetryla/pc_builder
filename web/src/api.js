const SESSION_KEY = "pc-builder-session";
let tokens = null;
try {
  tokens = JSON.parse(sessionStorage.getItem(SESSION_KEY));
} catch {
  /* No saved session. */
}
let refreshing = null;
let generation = 0;

export function hasSession() {
  return Boolean(tokens?.refresh_token);
}
export function setSession(value) {
  generation += 1;
  tokens = value;
  if (value) sessionStorage.setItem(SESSION_KEY, JSON.stringify(value));
  else sessionStorage.removeItem(SESSION_KEY);
}

async function send(path, method, body, access) {
  let response;
  try {
    response = await fetch(`/api/v1${path}`, {
      method,
      headers: {
        ...(body !== undefined && { "Content-Type": "application/json" }),
        ...(access && { Authorization: `Bearer ${access}` }),
      },
      ...(body !== undefined && { body: JSON.stringify(body) }),
    });
  } catch {
    throw new Error(
      "Nepavyko pasiekti serverio. Patikrinkite ryšį ir bandykite dar kartą.",
    );
  }
  const data = response.status === 204 ? null : await response.json();
  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((e) => `${e.loc.slice(1).join(".")}: ${e.msg}`).join("; ")
      : detail;
    throw Object.assign(new Error(message || "Užklausa nepavyko."), {
      status: response.status,
    });
  }
  return data;
}

export async function refreshSession() {
  if (!refreshing) {
    const current = generation;
    refreshing = (async () => {
      await Promise.resolve();
      try {
        if (!tokens?.refresh_token)
          throw Object.assign(new Error("Prisijunkite iš naujo."), {
            status: 401,
          });
        const next = await send("/auth/refresh", "POST", {
          refresh_token: tokens.refresh_token,
        });
        if (generation !== current)
          throw new Error("Sesija pasikeitė. Pakartokite veiksmą.");
        setSession(next);
        return next;
      } catch (error) {
        if (error.status === 401 && generation === current) {
          setSession(null);
          window.dispatchEvent(new Event("session-expired"));
        }
        throw error;
      } finally {
        refreshing = null;
      }
    })();
  }
  return refreshing;
}

export async function api(path, method = "GET", body, authenticated = true) {
  const access = authenticated ? tokens?.access_token : null;
  try {
    return await send(path, method, body, access);
  } catch (error) {
    if (!authenticated || error.status !== 401) throw error;
    // A concurrent request may already have rotated both tokens.
    if (tokens?.access_token === access) await refreshSession();
    try {
      return await send(path, method, body, tokens?.access_token);
    } catch (retryError) {
      if (retryError.status === 401) {
        setSession(null);
        window.dispatchEvent(new Event("session-expired"));
      }
      throw retryError;
    }
  }
}
