import { useEffect, useMemo, useRef, useState } from "react";
import { acknowledgeAlert, connectAlertsWebSocket, fetchAlerts } from "./api";
import "./styles.css";

const severityPriority = {
  EMERGENCY: 1,
  URGENT: 2,
  ROUTINE: 3
};

const severityLabel = {
  EMERGENCY: "HIGH",
  URGENT: "HIGH",
  ROUTINE: "MEDIUM"
};

function App() {
  const [alerts, setAlerts] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const notificationRef = useRef(null);

  useEffect(() => {
    let socket;

    async function loadData() {
      try {
        const initialAlerts = await fetchAlerts();
        setAlerts(initialAlerts);

        // Optional: preload open alerts into the notification panel
        setNotifications(initialAlerts.filter((a) => a.status === "open"));
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setLoading(false);
      }

      socket = connectAlertsWebSocket((event) => {
        if (event.type === "alert_created") {
          setAlerts((current) => [event.payload, ...current]);
          setNotifications((prev) => [event.payload, ...prev]);
        }

        if (event.type === "alert_acknowledged") {
          updateLocalAlertStatus(event.payload.alert_id);
        }
      });
    }

    loadData();
    return () => socket?.close();
  }, []);

  useEffect(() => {
    function handleClickOutside(event) {
      if (
        notificationRef.current &&
        !notificationRef.current.contains(event.target)
      ) {
        setShowNotifications(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const updateLocalAlertStatus = (id) => {
    setAlerts((current) =>
      current.map((a) =>
        a.alert_id === id ? { ...a, status: "acknowledged" } : a
      )
    );
    setNotifications((prev) => prev.filter((n) => n.alert_id !== id));
  };

  async function handleAcknowledge(alertId) {
    try {
      await acknowledgeAlert(alertId);
      updateLocalAlertStatus(alertId);
    } catch (ackError) {
      window.alert(ackError.message);
    }
  }

  const sortedAlerts = useMemo(() => {
    return [...alerts].sort((a, b) => {
      const severityDiff =
        severityPriority[a.severity] - severityPriority[b.severity];
      if (severityDiff !== 0) return severityDiff;
      return new Date(b.created_at) - new Date(a.created_at);
    });
  }, [alerts]);

  const totalActive = alerts.filter((a) => a.status === "open").length;
  const urgentCount = alerts.filter(
    (a) => a.status === "open" && a.severity !== "ROUTINE"
  ).length;
  const helpDispatched = alerts.filter(
    (a) => a.status === "acknowledged"
  ).length;

  if (loading) return <main className="layout">Loading alerts...</main>;

  return (
    <main className="layout">
      <nav className="navbar">
        <div className="nav-left">
          <div className="logo-icon">📞</div>
          <div className="brand-info">
            <h1>Helpline Dashboard</h1>
            <p className="operator-tag">Operator: x</p>
          </div>
        </div>

        <div className="nav-right">
          <div className="notification-trigger" ref={notificationRef}>
  <button
    className={`nav-icon-btn ${notifications.length > 0 ? "has-alerts" : ""}`}
    onClick={() => setShowNotifications((prev) => !prev)}
  >
    🔔
    {notifications.length > 0 && (
      <span className="badge-count">{notifications.length}</span>
    )}
  </button>

  {showNotifications && (
    <>
      <div
        className="notification-overlay-backdrop"
        onClick={() => setShowNotifications(false)}
      />

      <div
        className="notification-overlay-panel"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="notification-overlay-header">
          <h3>Active Call Notifications</h3>
          <span>{notifications.length} open</span>
        </div>

        <div className="notification-overlay-body">
          {notifications.length === 0 ? (
            <div className="notification-empty">No new active calls.</div>
          ) : (
            notifications.map((note) => (
              <div key={note.alert_id} className="notification-item">
                <div className="notification-item-top">
                  <strong>{note.alert_id}</strong>
                  <span
                    className={`badge-pill badge-${note.severity.toLowerCase()}`}
                  >
                    {severityLabel[note.severity] || note.severity}
                  </span>
                </div>

                <p className="notification-message">
                  {note.english_translation ||
                    note.transcript ||
                    "No call summary available."}
                </p>

                <div className="notification-meta">
                  <span>Device #{note.box_id}</span>
                  <span>
                    {note.created_at
                      ? new Date(note.created_at).toLocaleTimeString()
                      : "Unknown time"}
                  </span>
                </div>

                <button
                  className="notif-ack-btn"
                  onClick={() => handleAcknowledge(note.alert_id)}
                >
                  Acknowledge
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  )}
</div>

          <button className="sign-out-btn">
            <span className="signout-inner">
              <span className="signout-icon">↪</span>
              Sign Out
            </span>
          </button>
        </div>
      </nav>

      <section className="stats-row">
        <div className="stat-card">
          <div className="stat-info">
            <label>Total Active Calls</label>
            <span className="stat-value">{totalActive}</span>
          </div>
          <div className="stat-icon icon-blue">📞</div>
        </div>

        <div className="stat-card">
          <div className="stat-info">
            <label>Urgent Calls</label>
            <span className="stat-value text-red">{urgentCount}</span>
          </div>
          <div className="stat-icon icon-red">📞</div>
        </div>

        <div className="stat-card">
          <div className="stat-info">
            <label>Help Dispatched</label>
            <span className="stat-value text-green">{helpDispatched}</span>
          </div>
          <div className="stat-icon icon-green">📞</div>
        </div>
      </section>

      <h2 className="section-title">Active Calls</h2>
      {error && <p className="error">{error}</p>}

      <section className="cards">
        {sortedAlerts.map((alert) => (
          <article
            key={alert.alert_id}
            className={`active-call-card ${
              alert.status === "acknowledged" ? "acknowledged-dim" : ""
            }`}
          >
            <div className="alert-top">
              <div className="warning-circle">⚠</div>
            </div>

            <div className="call-heading">
              <h3>Call ID: {alert.alert_id}</h3>
              <span className={`badge-pill badge-${alert.severity.toLowerCase()}`}>
                {severityLabel[alert.severity] || alert.severity}
              </span>
            </div>

            <div className="field-group">
              <label>Resident</label>
              <p className="field-value">Resident Name (ID: {alert.box_id})</p>
            </div>

            <div className="summary-box">
              <label>Call Summary</label>
              <p>
                {alert.english_translation ||
                  alert.transcript ||
                  "No translation available."}
              </p>
            </div>

            <div className="detail-block">
              <label>Address</label>
              <p>Blk {alert.box_id} Sample Street, Singapore</p>
            </div>

            <div className="detail-block">
              <label>Device ID</label>
              <p>SeniorAid Button #{alert.box_id}</p>
            </div>

            <div className="detail-block">
              <label>Time Alerted</label>
              <p>
                {alert.created_at
                  ? new Date(alert.created_at).toLocaleString()
                  : "Unknown"}
              </p>
            </div>

            {alert.status === "open" ? (
              <button
                className="btn-ack"
                onClick={() => handleAcknowledge(alert.alert_id)}
              >
                Acknowledge
              </button>
            ) : (
              <button className="btn-ack btn-disabled" disabled>
                Acknowledged
              </button>
            )}
          </article>
        ))}
      </section>
    </main>
  );
}

export default App;