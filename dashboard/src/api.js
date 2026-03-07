const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
const protocol = window.location.protocol === "https:" ? "wss" : "ws";
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || `${protocol}://${window.location.host}`;
const API_BASE_URL_FALLBACK = null;

async function fetchWithLocalFallback(path, options) {
  try {
    return await fetch(`${API_BASE_URL}${path}`, options);
  } catch (primaryError) {
    if (!API_BASE_URL_FALLBACK) {
      throw primaryError;
    }
    return fetch(`${API_BASE_URL_FALLBACK}${path}`, options);
  }
}

export async function fetchAlerts() {
  let response;
  try {
    response = await fetchWithLocalFallback("/api/v1/alerts");
  } catch (error) {
    throw new Error(
      `Network error: dashboard cannot reach backend API. ` +
        `Ensure backend is running and reachable, then verify http://127.0.0.1:8000/health. ` +
        `Browser error: ${error?.message || "unknown"}`
    );
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Backend error while loading alerts (${response.status}): ${errorText}`);
  }

  return response.json();
}

export async function acknowledgeAlert(alertId) {
  let response;
  try {
    response = await fetchWithLocalFallback(`/api/v1/alerts/${alertId}/acknowledge`, {
      method: "PATCH"
    });
  } catch (error) {
    throw new Error(
      `Network error: dashboard cannot reach backend API. ` +
        `Ensure backend is running and reachable, then verify http://127.0.0.1:8000/health. ` +
        `Browser error: ${error?.message || "unknown"}`
    );
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Backend error while acknowledging alert (${response.status}): ${errorText}`);
  }

  return response.json();
}

export function connectAlertsWebSocket(onMessage) {
  const socket = new WebSocket(`${WS_BASE_URL}/api/v1/alerts/ws`);

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
