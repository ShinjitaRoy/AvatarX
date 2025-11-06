import React from 'react';
import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '1rem',
      backgroundColor: '#f8f9fa',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <Link to="/" style={{ fontSize: '1.5rem', fontWeight: 'bold', textDecoration: 'none', color: '#000' }}>
        AvatarX
      </Link>
      
      <div style={{ display: 'flex', gap: '2rem' }}>
        <Link to="/about" style={{ textDecoration: 'none', color: '#000' }}>About</Link>
        <Link to="/features" style={{ textDecoration: 'none', color: '#000' }}>Features</Link>
      </div>
      
      <div style={{ display: 'flex', gap: '1rem' }}>
        <Link to="/login" style={{ textDecoration: 'none', padding: '0.5rem 1rem', backgroundColor: '#007bff', color: '#fff', borderRadius: '4px' }}>
          Login
        </Link>
        <Link to="/register" style={{ textDecoration: 'none', padding: '0.5rem 1rem', backgroundColor: '#28a745', color: '#fff', borderRadius: '4px' }}>
          Register
        </Link>
      </div>
    </nav>
  );
}