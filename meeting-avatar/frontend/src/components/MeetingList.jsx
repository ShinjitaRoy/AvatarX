import React, { useEffect, useState } from "react";
import api from "../services/api";

export default function MeetingList() {
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState("");

  async function load() {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      if (!user.id) {
        setStatus("Please login first");
        return;
      }

      const res = await api.get("/list", { params: { user_id: user.id } });
      setItems(res.data.scheduled || []);
    } catch (err) {
      setStatus("Error loading list: " + (err.message || ""));
    }
  }

  useEffect(() => {
    load();
  }, []);

  const onLeave = async () => {
    setStatus("Leaving meeting...");
    try {
      const res = await api.post("/leave");
      setStatus(res.data.ok ? "Left meeting" : "Leave failed");
    } catch (err) {
      setStatus("Error leaving: " + (err.message || ""));
    }
  };

  return (
    <div>
      <h3>Scheduled meetings</h3>
      <ul>
        {items.length === 0 && <li>No scheduled meetings</li>}
        {items.map((it, idx) => (
          <li key={idx}>
            {it.meeting_id} at {it.start_time} {it.password ? "(has password)" : ""}
          </li>
        ))}
      </ul>
      <div style={{ marginTop: 8 }}>
        <button onClick={load}>Refresh</button>{" "}
        <button onClick={onLeave}>Leave Current Meeting</button>
      </div>
      <div style={{ marginTop: 8 }}>{status}</div>
    </div>
  );
}