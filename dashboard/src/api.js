const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
const protocol = window.location.protocol === "https:" ? "wss" : "ws";
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || `${protocol}://${window.location.host}`;

const AUTH_STORAGE_KEY = "senioraid_auth";

function buildUrl(path) {
  return `${API_BASE_URL}${path}`;
}

export function getStoredAuth() {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function storeAuth(authPayload) {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authPayload));
}

export function clearStoredAuth() {
  localStorage.removeItem(AUTH_STORAGE_KEY);
}

function getAuthHeaders() {
  const auth = getStoredAuth();
  if (!auth?.access_token) {
    return {};
  }
  return {
    Authorization: `Bearer ${auth.access_token}`
  };
}

export async function loginUser(email, password) {
  const response = await fetch(buildUrl("/api/v1/auth/login"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ email, password })
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Wrong email and/or password");
    }
    const errorText = await response.text();
    throw new Error(`Login failed (${response.status}): ${errorText}`);
  }

  const payload = await response.json();
  storeAuth(payload);
  return payload;
}

export async function fetchCurrentUser() {
  const response = await fetch(buildUrl("/api/v1/auth/me"), {
    headers: {
      ...getAuthHeaders()
    }
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearStoredAuth();
    }
    const errorText = await response.text();
    throw new Error(`Session check failed (${response.status}): ${errorText}`);
  }

  return response.json();
}

export async function fetchAlerts() {
  let response;
  try {
    response = await fetch(buildUrl("/api/v1/alerts"), {
      headers: {
        ...getAuthHeaders()
      }
    });
  } catch (error) {
    throw new Error(
      `Network error: dashboard cannot reach backend API. Ensure backend is running, then verify http://127.0.0.1:8000/health. Browser error: ${error?.message || "unknown"}`
    );
  }

  if (!response.ok) {
    if (response.status === 401) {
      clearStoredAuth();
    }
    const errorText = await response.text();
    throw new Error(`Backend error while loading alerts (${response.status}): ${errorText}`);
  }

  return response.json();
}

export async function acknowledgeAlert(alertId) {
  let response;
  try {
    response = await fetch(buildUrl(`/api/v1/alerts/${alertId}/acknowledge`), {
      method: "PATCH",
      headers: {
        ...getAuthHeaders()
      }
    });
  } catch (error) {
    throw new Error(
      `Network error: dashboard cannot reach backend API. Ensure backend is running, then verify http://127.0.0.1:8000/health. Browser error: ${error?.message || "unknown"}`
    );
  }

  if (!response.ok) {
    if (response.status === 401) {
      clearStoredAuth();
    }
    const errorText = await response.text();
    throw new Error(`Backend error while acknowledging alert (${response.status}): ${errorText}`);
  }

  return response.json();
}

export function connectAlertsWebSocket(onMessage) {
  const auth = getStoredAuth();
  if (!auth?.access_token) {
    throw new Error("Authentication token is missing.");
  }

  const tokenQuery = encodeURIComponent(auth.access_token);
  const socket = new WebSocket(`${WS_BASE_URL}/api/v1/alerts/ws?token=${tokenQuery}`);

  socket.onmessage = (event) => {
    try {
      const parsed = JSON.parse(event.data);
      onMessage(parsed);
    } catch (error) {
      console.error("Invalid websocket payload", error);
    }
  };

  const pingInterval = setInterval(() => {
    if (socket.readyState === WebSocket.OPEN) {
      socket.send("ping");
    }
  }, 20000);

  socket.onclose = () => clearInterval(pingInterval);
  return socket;
}
