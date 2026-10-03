import { NavLink, useLocation } from 'react-router-dom';

const navItems = [
  { section: 'Overview', items: [
    { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  ]},
  { section: 'Monitoring', items: [
    { to: '/transactions', label: 'Transactions', icon: '💳' },
    { to: '/alerts', label: 'Alerts', icon: '🔔' },
    { to: '/investigations', label: 'Investigations', icon: '🔍' },
  ]},
  { section: 'Analysis', items: [
    { to: '/network', label: 'Network', icon: '🕸️' },
    { to: '/reports', label: 'Reports', icon: '📈' },
  ]},
];

export default function Sidebar({ user, onLogout }) {
  const location = useLocation();

  return (
    <nav className="sidebar">
      <div className="sidebar-logo">
        <h2 style={{ fontSize: '13px', lineHeight: '1.3', margin: 0, fontWeight: 700, letterSpacing: '-0.01em' }}>
          AI-Driven Fraud Detection
        </h2>
        <span style={{ fontSize: '10px', color: '#6366f1', fontWeight: 600, letterSpacing: '0.04em' }}>
          AND PREVENTION SYSTEM
        </span>
      </div>

      <div className="sidebar-nav">
        {navItems.map((section) => (
          <div key={section.section} className="sidebar-section">
            <div className="sidebar-section-label">{section.section}</div>
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `sidebar-link${isActive ? ' active' : ''}`
                }
              >
                <span>{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-user-avatar">
            {user.full_name?.charAt(0) || 'U'}
          </div>
          <div className="sidebar-user-info">
            <div className="sidebar-user-name">{user.full_name}</div>
            <div className="sidebar-user-role">{user.role}</div>
          </div>
          <button className="sidebar-logout" onClick={onLogout}>
            Exit
          </button>
        </div>
      </div>
    </nav>
  );
}
