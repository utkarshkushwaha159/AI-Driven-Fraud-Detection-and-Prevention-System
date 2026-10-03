import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAlerts, updateAlert } from '../services/api';
import { StatusBadge, ProbabilityBar, LoadingState, EmptyState } from '../components/SharedComponents';

export default function Alerts() {
  const [data, setData] = useState({ alerts: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const navigate = useNavigate();
  const pageSize = 20;

  useEffect(() => { load(); }, [page, statusFilter, severityFilter]);

  const load = async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize };
      if (statusFilter !== 'all') params.status = statusFilter;
      if (severityFilter !== 'all') params.severity = severityFilter;
      const res = await getAlerts(params);
      setData(res.data);
    } catch { }
    setLoading(false);
  };

  const handleStatusChange = async (alertId, newStatus) => {
    try {
      await updateAlert(alertId, newStatus);
      load();
    } catch { }
  };

  const totalPages = Math.ceil(data.total / pageSize);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Fraud Alerts</h1>
        <p>Review and manage security alerts</p>
      </div>

      <div className="card">
        <div className="filter-bar">
          <select className="form-select" style={{ width: 160 }}
            value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
            <option value="all">All Status</option>
            <option value="new">New</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
            <option value="dismissed">Dismissed</option>
          </select>
          <select className="form-select" style={{ width: 160 }}
            value={severityFilter} onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }}>
            <option value="all">All Severity</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>

        {loading ? <LoadingState /> : data.alerts.length === 0 ? (
          <EmptyState icon="🔔" title="No alerts" message="No alerts match your criteria." />
        ) : (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Severity</th>
                    <th>Amount</th>
                    <th>Fraud Probability</th>
                    <th>Anomaly Score</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data.alerts.map((a) => (
                    <tr key={a.id}>
                      <td><StatusBadge status={a.severity} /></td>
                      <td style={{ fontWeight: 600 }}>₹{a.transaction_amount?.toFixed(2) || '—'}</td>
                      <td><ProbabilityBar value={a.fraud_probability} /></td>
                      <td>{a.anomaly_score != null ? `${(a.anomaly_score * 100).toFixed(0)}%` : '—'}</td>
                      <td><StatusBadge status={a.status} /></td>
                      <td className="text-sm text-muted">
                        {a.created_at ? new Date(a.created_at).toLocaleDateString() : '—'}
                      </td>
                      <td>
                        <div className="flex gap-2">
                          <button className="btn btn-sm btn-ghost"
                            onClick={() => navigate(`/transactions/${a.transaction_id}`)}>
                            View
                          </button>
                          {a.status === 'new' && (
                            <button className="btn btn-sm btn-secondary"
                              onClick={() => handleStatusChange(a.id, 'acknowledged')}>
                              Acknowledge
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination">
              <span>{data.total} alert(s)</span>
              <div className="pagination-buttons">
                <button className="btn btn-sm btn-secondary" disabled={page <= 1}
                  onClick={() => setPage(p => p - 1)}>Previous</button>
                <button className="btn btn-sm btn-secondary" disabled={page >= totalPages}
                  onClick={() => setPage(p => p + 1)}>Next</button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
