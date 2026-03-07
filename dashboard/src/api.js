const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");

export async function fetchAlerts() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/alerts`);
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to load alerts (${response.status}): ${errorText}`);
    }
    return response.json();
  } catch (error) {
    throw new Error(
      `Network error: dashboard cannot reach ${API_BASE_URL}. ` +
        `Ensure backend is running and reachable, then verify ${API_BASE_URL}/health.`
    );
  }
}

export async function acknowledgeAlert(alertId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/alerts/${alertId}/acknowledge`, {
      method: "PATCH"
    });
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to acknowledge alert (${response.status}): ${errorText}`);
    }
    return response.json();
  } catch (error) {
    throw new Error(
      `Network error: dashboard cannot reach ${API_BASE_URL}. ` +
        `Ensure backend is running and reachable, then verify ${API_BASE_URL}/health.`
    );
  }
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
