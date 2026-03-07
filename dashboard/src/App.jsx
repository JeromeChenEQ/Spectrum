import { useEffect, useMemo, useRef, useState } from "react";
import { acknowledgeAlert, connectAlertsWebSocket, fetchAlerts } from "./api";
import "./styles.css";

const classificationPriority = {
  URGENT: 1,
  UNCERTAIN: 2,
  "NON-URGENT": 3
};

function normalizeClassification(rawValue) {
  const normalized = (rawValue ?? "")
    .toString()
    .trim()
    .toUpperCase()
    .replace(/_/g, "-")
    .replace(/\s+/g, "-");

  if (["URGENT", "UNCERTAIN", "NON-URGENT"].includes(normalized)) {
    return normalized;
  }

  if (normalized === "EMERGENCY" || normalized === "HIGH") {
    return "URGENT";
  }

  if (normalized === "ROUTINE" || normalized === "LOW" || normalized === "NONURGENT") {
    return "NON-URGENT";
  }

  return "UNCERTAIN";
}

function getAlertClassification(alert) {
  return normalizeClassification(
    alert.final_classification ?? alert.classification ?? alert.severity
  );
}

function getPrimaryActionLabel(alert) {
  const classification = getAlertClassification(alert);
  if (classification === "URGENT") return "Dispatch Help";
  if (classification === "UNCERTAIN") return "Investigate";
  return "Acknowledge";
}

function getCompletedActionLabel(alert) {
  return getAlertClassification(alert) === "URGENT" ? "Dispatched" : "Acknowledged";
}

function getAlertDialect(alert) {
  return alert.dialect ?? alert.language ?? alert.detected_language ?? alert.lang ?? "Unknown";
}

function PhoneIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" width="30" height="30">
      <path
        d="M20.5 16.7v2.5a1.7 1.7 0 0 1-1.8 1.7A16.9 16.9 0 0 1 3.1 5.3 1.7 1.7 0 0 1 4.8 3.5h2.5a1.7 1.7 0 0 1 1.6 1.4l.4 2a1.7 1.7 0 0 1-.5 1.6l-1.1 1.1a13.4 13.4 0 0 0 6.7 6.7l1.1-1.1a1.7 1.7 0 0 1 1.6-.5l2 .4a1.7 1.7 0 0 1 1.4 1.6Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function BellIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" width="20" height="20">
      <path
        d="M7 10.2a5 5 0 1 1 10 0v3.1c0 .9.3 1.7.9 2.4l.9 1H5.2l.9-1c.6-.7.9-1.5.9-2.4v-3.1Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M10 17.1a2 2 0 0 0 4 0"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
      <path d="M12 3.8v1.5" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

function SignOutIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" width="20" height="20">
      <path
        d="M10 4.5H6.7A2.2 2.2 0 0 0 4.5 6.7v10.6a2.2 2.2 0 0 0 2.2 2.2H10"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.9"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M12 12h7.2M16.8 8.2 20.5 12l-3.7 3.8"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.9"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function App() {
  const [alerts, setAlerts] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [incomingCallNotices, setIncomingCallNotices] = useState([]);
  const [actionToasts, setActionToasts] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [selectedTab, setSelectedTab] = useState("active");
  const [investigationAlert, setInvestigationAlert] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const notificationRef = useRef(null);
  const userMenuRef = useRef(null);
  const toastTimerRef = useRef(new Set());

  const updateLocalAlertStatus = (id) => {
    setAlerts((current) => current.map((a) => (a.alert_id === id ? { ...a, status: "acknowledged" } : a)));
    setNotifications((prev) => prev.filter((n) => n.alert_id !== id));
  };

  useEffect(() => {
    let socket;

    async function loadData() {
      try {
        const initialAlerts = await fetchAlerts();
        setAlerts(initialAlerts);
        setNotifications(initialAlerts.filter((a) => a.status === "open"));
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setLoading(false);
      }

      socket = connectAlertsWebSocket((event) => {
        if (event.type === "alert_created") {
          const alert = event.payload;
          setAlerts((current) => [alert, ...current]);
          setNotifications((prev) => [alert, ...prev]);
          setIncomingCallNotices((current) => [
            {
              id: `${alert.alert_id}-${Date.now()}-${Math.random()}`,
              alertId: alert.alert_id,
              message: alert.english_translation || alert.transcript || "A new call was received.",
              createdAt: alert.created_at
            },
            ...current
          ]);
        }

        if (event.type === "alert_acknowledged") {
          updateLocalAlertStatus(event.payload.alert_id);
        }
      });
    }

    loadData();

    const interval = setInterval(async () => {
      try {
        const updatedAlerts = await fetchAlerts();
        setAlerts(updatedAlerts);
        setNotifications(updatedAlerts.filter((a) => a.status === "open"));
      } catch {
        // Polling failures should not crash UI.
      }
    }, 3000);

    return () => {
      socket?.close();
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    function handleClickOutside(event) {
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    return () => {
      toastTimerRef.current.forEach((timerId) => window.clearTimeout(timerId));
      toastTimerRef.current.clear();
    };
  }, []);

  function acknowledgeIncomingNotice(noticeId) {
    setIncomingCallNotices((current) => current.filter((notice) => notice.id !== noticeId));
  }

  function showActionSuccessToast(message) {
    const toastId = `${Date.now()}-${Math.random()}`;
    setActionToasts((current) => [...current, { id: toastId, message }]);
    const timerId = window.setTimeout(() => {
      setActionToasts((current) => current.filter((toast) => toast.id !== toastId));
      toastTimerRef.current.delete(timerId);
    }, 5000);
    toastTimerRef.current.add(timerId);
  }

  async function handleAcknowledge(alertId, successMessage = "Action successful.") {
    try {
      await acknowledgeAlert(alertId);
      updateLocalAlertStatus(alertId);
      showActionSuccessToast(successMessage);
      return true;
    } catch (ackError) {
      window.alert(ackError.message);
      return false;
    }
  }

  function closeInvestigateModal() {
    setInvestigationAlert(null);
  }

  async function handleInvestigateDecision() {
    if (!investigationAlert) return;
    const success = await handleAcknowledge(
      investigationAlert.alert_id,
      `Alert ${investigationAlert.alert_id} acknowledged successfully.`
    );
    if (success) closeInvestigateModal();
  }

  function promoteAlertToUrgent(alertId) {
    setAlerts((current) => current.map((a) => (a.alert_id === alertId ? { ...a, final_classification: "URGENT" } : a)));
    setNotifications((current) =>
      current.map((n) => (n.alert_id === alertId ? { ...n, final_classification: "URGENT" } : n))
    );
    setInvestigationAlert((current) =>
      current && current.alert_id === alertId ? { ...current, final_classification: "URGENT" } : current
    );
  }

  async function handleInvestigateDispatch() {
    if (!investigationAlert) return;
    promoteAlertToUrgent(investigationAlert.alert_id);
    const success = await handleAcknowledge(
      investigationAlert.alert_id,
      `Dispatch help successful for alert ${investigationAlert.alert_id}.`
    );
    if (success) closeInvestigateModal();
  }

  async function handleInvestigateAcknowledge() {
    await handleInvestigateDecision();
  }

  function handlePrimaryAction(alert) {
    const classification = getAlertClassification(alert);
    if (classification === "UNCERTAIN") {
      setInvestigationAlert(alert);
      return;
    }
    const successMessage =
      classification === "URGENT"
        ? `Dispatch help successful for alert ${alert.alert_id}.`
        : `Alert ${alert.alert_id} acknowledged successfully.`;
    handleAcknowledge(alert.alert_id, successMessage);
  }

  const sortedAlerts = useMemo(() => {
    return [...alerts].sort((a, b) => {
      const classificationDiff =
        classificationPriority[getAlertClassification(a)] - classificationPriority[getAlertClassification(b)];
      if (classificationDiff !== 0) return classificationDiff;
      return new Date(b.created_at) - new Date(a.created_at);
    });
  }, [alerts]);

  const activeCount = alerts.filter((a) => a.status === "open").length;
  const urgentCount = alerts.filter((a) => a.status === "open" && getAlertClassification(a) === "URGENT").length;
  const uncertainCount = alerts.filter((a) => a.status === "open" && getAlertClassification(a) === "UNCERTAIN").length;
  const nonUrgentCount = alerts.filter((a) => a.status === "open" && getAlertClassification(a) === "NON-URGENT").length;
  const visibleAlerts = sortedAlerts.filter((a) => (selectedTab === "active" ? a.status === "open" : a.status === "acknowledged"));

  if (loading) return <main className="layout">Loading alerts...</main>;

  return (
    <main className="layout">
      <nav className="navbar">
        <div className="nav-left">
          <div className="logo-icon">
            <PhoneIcon />
          </div>
          <div className="brand-info">
            <h1>Personal Alert Button Dashboard</h1>
          </div>
        </div>

        <div className="nav-right">
          <div className="notification-trigger" ref={notificationRef}>
            <button
              className={`nav-icon-btn ${notifications.length > 0 ? "has-alerts" : ""}`}
              onClick={() => setShowNotifications((prev) => !prev)}
            >
              <BellIcon />
              {notifications.length > 0 && <span className="badge-count">{notifications.length}</span>}
            </button>

            {showNotifications && (
              <div className="notification-overlay-panel" onClick={(e) => e.stopPropagation()}>
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
                          <span className={`badge-pill badge-${getAlertClassification(note).toLowerCase()}`}>
                            {getAlertClassification(note)}
                          </span>
                        </div>

                        <p className="notification-message">
                          {note.english_translation || note.transcript || "No call summary available."}
                        </p>

                        <div className="notification-meta">
                          <span>Device #{note.box_id}</span>
                          <span>
                            {note.created_at ? new Date(note.created_at).toLocaleTimeString() : "Unknown time"}
                          </span>
                        </div>

                        <button className="notif-ack-btn" onClick={() => handlePrimaryAction(note)}>
                          {getPrimaryActionLabel(note)}
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="user-menu" ref={userMenuRef}>
            <button className="user-menu-btn" onClick={() => setShowUserMenu((prev) => !prev)}>
              <span className="signout-inner">
                User
                <span className="signout-icon">
                  <SignOutIcon />
                </span>
              </span>
            </button>
            {showUserMenu && (
              <div className="user-menu-dropdown">
                <button className="user-menu-item" onClick={() => setShowUserMenu(false)}>
                  Log Out
                </button>
              </div>
            )}
          </div>
        </div>
      </nav>

      {incomingCallNotices.length > 0 && (
        <div className="notification-stack" aria-live="assertive">
          {incomingCallNotices.map((notice) => (
            <div key={notice.id} className="notif-card">
              <div className="notif-content">
                <strong>New Call: {notice.alertId}</strong>
                <p>{notice.message}{notice.createdAt ? ` (${new Date(notice.createdAt).toLocaleTimeString()})` : ""}</p>
              </div>
              <button className="notif-ack-btn" onClick={() => acknowledgeIncomingNotice(notice.id)}>
                Acknowledge
              </button>
            </div>
          ))}
        </div>
      )}

      {actionToasts.length > 0 && (
        <div className="action-toast-stack" aria-live="polite" aria-atomic="true">
          {actionToasts.map((toast) => (
            <div key={toast.id} className="action-toast">
              <strong>Success</strong>
              <p>{toast.message}</p>
            </div>
          ))}
        </div>
      )}

      <section className="stats-row">
        <div className="stat-card">
          <div className="stat-info">
            <label>Urgent Calls</label>
            <span className="stat-value text-red">{urgentCount}</span>
          </div>
          <div className="stat-icon icon-red"><PhoneIcon /></div>
        </div>

        <div className="stat-card">
          <div className="stat-info">
            <label>Uncertain Calls</label>
            <span className="stat-value text-yellow">{uncertainCount}</span>
          </div>
          <div className="stat-icon icon-yellow"><PhoneIcon /></div>
        </div>

        <div className="stat-card">
          <div className="stat-info">
            <label>Non-Urgent Calls</label>
            <span className="stat-value text-green">{nonUrgentCount}</span>
          </div>
          <div className="stat-icon icon-green"><PhoneIcon /></div>
        </div>
      </section>

      <div className="alerts-tabs" role="tablist" aria-label="Alert categories">
        <button
          type="button"
          role="tab"
          aria-selected={selectedTab === "active"}
          className={`alerts-tab ${selectedTab === "active" ? "is-active" : ""}`}
          onClick={() => setSelectedTab("active")}
        >
          Active Calls <span className="tab-badge">{activeCount}</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={selectedTab === "completed"}
          className={`alerts-tab ${selectedTab === "completed" ? "is-active" : ""}`}
          onClick={() => setSelectedTab("completed")}
        >
          Completed
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      <section className="cards">
        {visibleAlerts.length === 0 && (
          <p className="cards-empty">
            {selectedTab === "active" ? "No active calls right now." : "No completed calls yet."}
          </p>
        )}

        {visibleAlerts.map((alert) => (
          <article
            key={alert.alert_id}
            className={`active-call-card ${alert.status === "acknowledged" ? "acknowledged-dim" : ""}`}
          >
            <div className="call-heading">
              <div className="warning-circle">?</div>
              <div className="call-heading-main">
                <h3>Call ID: {alert.alert_id}</h3>
                <span className={`badge-pill badge-${getAlertClassification(alert).toLowerCase()}`}>
                  {getAlertClassification(alert)}
                </span>
              </div>
            </div>

            <div className="summary-box">
              <label>Call Summary</label>
              <p>{alert.english_translation || alert.transcript || "No translation available."}</p>
            </div>

            <div className="detail-block">
              <label>Dialect</label>
              <p>{getAlertDialect(alert)}</p>
            </div>

            <div className="field-group">
              <label>Resident</label>
              <p className="field-value">Resident Name (ID: {alert.box_id})</p>
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
              <p>{alert.created_at ? new Date(alert.created_at).toLocaleString() : "Unknown"}</p>
            </div>

            {alert.status === "open" ? (
              <button className="btn-ack" onClick={() => handlePrimaryAction(alert)}>
                {getPrimaryActionLabel(alert)}
              </button>
            ) : (
              <button className="btn-ack btn-disabled" disabled>
                {getCompletedActionLabel(alert)}
              </button>
            )}
          </article>
        ))}
      </section>

      {investigationAlert && (
        <div className="investigate-modal-backdrop" onClick={closeInvestigateModal}>
          <div className="investigate-modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-labelledby="investigate-modal-title">
            <div className="investigate-modal-header">
              <h3 id="investigate-modal-title">Investigate Alert {investigationAlert.alert_id}</h3>
            </div>

            <div className="investigate-modal-body">
              <div className="investigate-section">
                <label>Full Transcript</label>
                <p>{investigationAlert.transcript || "No transcript available."}</p>
              </div>

              <div className="investigate-section">
                <label>English Translation</label>
                <p>{investigationAlert.english_translation || "No translation available."}</p>
              </div>
            </div>

            <div className="investigate-modal-actions">
              <button className="btn-ack" onClick={handleInvestigateDispatch}>Dispatch Help</button>
              <button className="btn-ack" onClick={handleInvestigateAcknowledge}>Acknowledge</button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

export default App;