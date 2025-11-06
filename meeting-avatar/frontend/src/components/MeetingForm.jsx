import React, { useState } from "react";
import api from "../services/api";

export default function MeetingForm() {
  const [meetingId, setMeetingId] = useState("");
  const [password, setPassword] = useState("");
  const [startTime, setStartTime] = useState("");
  const [status, setStatus] = useState("");

  const onSchedule = async (e) => {
    e.preventDefault();
    if (!meetingId || !startTime) {
      setStatus("Meeting ID and start time required");
      return;
    }

    // Get user from localStorage
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (!user.id) {
      setStatus("Please login first");
      return;
    }

    setStatus("Scheduling...");
    try {
      const res = await api.post("/schedule", { 
        meeting_id: meetingId, 
        password, 
        start_time: startTime,
        user_id: user.id  // Include user ID
      });
      setStatus("Scheduled: " + JSON.stringify(res.data.scheduled));
    } catch (err) {
      setStatus("Error scheduling: " + (err.response?.data?.error || err.message));
    }
  };

  const onStartNow = async (e) => {
    e.preventDefault();
    if (!meetingId) {
      setStatus("Meeting ID required to start now");
      return;
    }
    setStatus("Starting meeting...");
    try {
      const res = await api.post("/start", { meeting_id: meetingId, password });
      setStatus(res.data.ok ? "Started" : "Start failed");
    } catch (err) {
      setStatus("Error starting: " + (err.response?.data?.error || err.message));
    }
  };

  return (
    <form onSubmit={onSchedule} style={{ display: "grid", gap: 8 }}>
      <label>
        Meeting ID
        <input value={meetingId} onChange={(e) => setMeetingId(e.target.value)} style={{ width: "100%" }} />
      </label>
      <label>
        Password
        <input value={password} onChange={(e) => setPassword(e.target.value)} style={{ width: "100%" }} />
      </label>
      <label>
        Start time (HH:MM, 24h)
        <input value={startTime} onChange={(e) => setStartTime(e.target.value)} placeholder="14:30" style={{ width: "100%" }} />
      </label>
      <div style={{ display: "flex", gap: 8 }}>
        <button type="submit">Schedule</button>
        <button type="button" onClick={onStartNow}>Start Now</button>
      </div>
      <div style={{ marginTop: 8 }}>{status}</div>
    </form>
  );
}