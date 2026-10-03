import { NavLink } from 'react-router-dom';

export default function Navbar({ user, onLogout }) {
  return (
    <nav className="navbar">
      <div className="navbar-brand" style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 700, fontSize: '15px' }}>
        <span style={{ fontSize: '18px' }}>🛡️</span>
        <span>AI-Driven Fraud Detection and Prevention System</span>
      </div>
      <div className="navbar-actions">
        <NavLink to="/payment" className={({ isActive }) => `navbar-link${isActive ? ' active' : ''}`}>
          Make Payment
        </NavLink>
        <NavLink to="/my-transactions" className={({ isActive }) => `navbar-link${isActive ? ' active' : ''}`}>
          My Transactions
        </NavLink>
        <span className="text-sm text-muted" style={{ marginLeft: 8 }}>
          {user.full_name}
        </span>
        <button className="btn btn-sm btn-secondary" onClick={onLogout}>Logout</button>
      </div>
    </nav>
  );
}
