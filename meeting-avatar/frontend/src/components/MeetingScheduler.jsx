import React from 'react';
import MeetingForm from './MeetingForm';
import MeetingList from './MeetingList';

export default function MeetingScheduler() {
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  return (
    <div style={{ maxWidth: 800, margin: '40px auto', padding: '20px' }}>
      <div style={{ marginBottom: '20px' }}>
        <h2>Meeting Scheduler</h2>
        <p>Welcome, {user.name || 'User'}!</p>
      </div>

      <div style={{ 
        display: 'grid',
        gap: '2rem',
        padding: '20px',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <section>
          <h3>Schedule New Meeting</h3>
          <MeetingForm />
        </section>

        <section>
          <h3>Your Meetings</h3>
          <MeetingList />
        </section>
      </div>
    </div>
  );
}