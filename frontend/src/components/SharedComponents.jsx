export function RiskBadge({ level }) {
  const label = (level || 'unknown').replace('_', ' ');
  return <span className={`badge badge-${level || 'pending'}`}>{label}</span>;
}

export function StatusBadge({ status }) {
  const label = (status || 'unknown').replace('_', ' ');
  return <span className={`badge badge-${status || 'pending'}`}>{label}</span>;
}

export function ProbabilityBar({ value }) {
  const pct = Math.round((value || 0) * 100);
  const level = pct >= 60 ? 'high' : pct >= 30 ? 'medium' : 'low';
  return (
    <div className="probability-bar">
      <div className="probability-track">
        <div
          className={`probability-fill ${level}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`probability-value text-${level === 'high' ? 'danger' : level === 'medium' ? 'warning' : 'success'}`}>
        {pct}%
      </span>
    </div>
  );
}

export function LoadingState({ message }) {
  return (
    <div className="loading-container">
      <div className="loading-spinner" />
      <p>{message || 'Loading...'}</p>
    </div>
  );
}

export function EmptyState({ icon, title, message }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">{icon || '📭'}</div>
      <h3>{title || 'No data'}</h3>
      <p>{message || 'Nothing to display.'}</p>
    </div>
  );
}

export function StatCard({ label, value, change, type }) {
  return (
    <div className="stat-card">
      <div className="stat-card-label">{label}</div>
      <div className="stat-card-value">{value}</div>
      {change !== undefined && (
        <div className={`stat-card-change ${type || ''}`}>{change}</div>
      )}
    </div>
  );
}
