const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");

export async function fetchAlerts() {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/alerts`);
  } catch (error) {
    throw new Error(
      `Network error: dashboard cannot reach ${API_BASE_URL}. ` +
        `Ensure backend is running and reachable, then verify ${API_BASE_URL}/health.`
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
    response = await fetch(`${API_BASE_URL}/api/v1/alerts/${alertId}/acknowledge`, {
      method: "PATCH"
    });
  } catch (error) {
    throw new Error(
      `Network error: dashboard cannot reach ${API_BASE_URL}. ` +
        `Ensure backend is running and reachable, then verify ${API_BASE_URL}/health.`
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
