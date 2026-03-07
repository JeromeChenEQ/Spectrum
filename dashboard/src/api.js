const API_BASE_URL = "http://localhost:8000";

export async function fetchAlerts() {
  const response = await fetch(`${API_BASE_URL}/api/v1/alerts`);
  if (!response.ok) {
    throw new Error("Failed to load alerts");
  }
  return response.json();
}

export async function acknowledgeAlert(alertId) {
  const response = await fetch(`${API_BASE_URL}/api/v1/alerts/${alertId}/acknowledge`, {
    method: "PATCH"
  });
  if (!response.ok) {
    throw new Error("Failed to acknowledge alert");
  }
  return response.json();
}

export function connectAlertsWebSocket(onMessage) {
  const socket = new WebSocket("ws://localhost:8000/api/v1/alerts/ws");

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