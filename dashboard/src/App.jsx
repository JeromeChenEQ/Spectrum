import { useEffect, useMemo, useState } from "react";

import { acknowledgeAlert, connectAlertsWebSocket, fetchAlerts } from "./api";

const severityPriority = {
  EMERGENCY: 1,
  URGENT: 2,
  ROUTINE: 3
};

function App() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let socket;

    async function loadData() {
      try {
        const initialAlerts = await fetchAlerts();
        setAlerts(initialAlerts);
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setLoading(false);
      }

      socket = connectAlertsWebSocket((event) => {
        if (event.type === "alert_created") {
          setAlerts((current) => [event.payload, ...current]);
        }

        if (event.type === "alert_acknowledged") {
          setAlerts((current) =>
            current.map((alert) =>
              alert.alert_id === event.payload.alert_id
                ? { ...alert, status: "acknowledged" }
                : alert
            )
          );
        }
      });
    }

    loadData();

    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, []);

  const sortedAlerts = useMemo(() => {
    return [...alerts].sort((a, b) => {
      const severityDiff = severityPriority[a.severity] - severityPriority[b.severity];
      if (severityDiff !== 0) {
        return severityDiff;
      }
      return new Date(b.created_at) - new Date(a.created_at);
    });
  }, [alerts]);

  async function handleAcknowledge(alertId) {
    try {
      await acknowledgeAlert(alertId);
      setAlerts((current) =>
        current.map((alert) =>
          alert.alert_id === alertId ? { ...alert, status: "acknowledged" } : alert
        )
      );
    } catch (ackError) {
      window.alert(ackError.message);
    }
  }

  if (loading) {
    return <main className="layout">Loading alerts...</main>;
  }

  return (
    <main className="layout">
      <h1>SeniorAid Helpdesk Dashboard</h1>
      <p className="subtitle">Realtime alert triage for elderly emergency button system</p>
      {error ? <p className="error">{error}</p> : null}

      <section className="cards">
        {sortedAlerts.map((alert) => (
          <article key={alert.alert_id} className={`card severity-${alert.severity.toLowerCase()}`}>
            <header className="card-header">
              <span className="badge">{alert.severity}</span>
              <span>Status: {alert.status}</span>
            </header>

            <p><strong>Alert ID:</strong> {alert.alert_id}</p>
            <p><strong>Box ID:</strong> {alert.box_id}</p>
            <p><strong>Language:</strong> {alert.detected_language}</p>
            <p><strong>Original Transcript:</strong> {alert.transcript}</p>
            <p><strong>English Translation:</strong> {alert.english_translation}</p>
            <p><strong>Created At:</strong> {new Date(alert.created_at).toLocaleString()}</p>

            {alert.status === "open" ? (
              <button onClick={() => handleAcknowledge(alert.alert_id)}>Acknowledge</button>
            ) : (
              <button disabled>Acknowledged</button>
            )}
          </article>
        ))}
      </section>
    </main>
  );
}

export default App;