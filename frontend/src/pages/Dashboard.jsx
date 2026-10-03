import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDashboardStats } from '../services/api';
import { StatCard, LoadingState, RiskBadge, ProbabilityBar, StatusBadge } from '../components/SharedComponents';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const PIE_COLORS = ['#059669', '#d97706', '#dc2626'];

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const res = await getDashboardStats();
      setData(res.data);
    } catch (err) {
      setError('Failed to load dashboard data. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingState message="Loading dashboard..." />;
  if (error) return <div className="page-container"><div className="login-error">{error}</div></div>;
  if (!data) return null;

  const { stats, trends, risk_distribution, recent_alerts, high_risk_transactions } = data;

  const riskPieData = [
    { name: 'Safe', value: risk_distribution?.safe || 0 },
    { name: 'Suspicious', value: risk_distribution?.suspicious || 0 },
    { name: 'High Risk', value: risk_distribution?.high_risk || 0 },
  ].filter(d => d.value > 0);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Fraud monitoring overview</p>
      </div>

      <div className="stats-grid">
        <StatCard label="Total Transactions" value={stats.total_transactions.toLocaleString()} />
        <StatCard label="Approved" value={stats.approved_transactions.toLocaleString()} />
        <StatCard label="Suspicious" value={stats.suspicious_transactions} />
        <StatCard label="Held / Blocked" value={stats.held_transactions + stats.blocked_transactions} />
        <StatCard label="Active Alerts" value={stats.total_alerts} />
        <StatCard label="Open Investigations" value={stats.open_investigations} />
        <StatCard label="Fraud Rate" value={`${(stats.fraud_rate * 100).toFixed(1)}%`} />
        <StatCard label="Total Volume" value={`₹${stats.total_amount.toLocaleString()}`} />
      </div>

      <div className="charts-grid">
        <div className="card">
          <div className="card-header">
            <div className="card-title">Transaction Trends</div>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(d) => d.slice(5)} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area type="monotone" dataKey="total" stroke="#2563eb" fill="#eff6ff" name="Total" />
              <Area type="monotone" dataKey="fraud" stroke="#dc2626" fill="#fef2f2" name="Held" />
              <Area type="monotone" dataKey="suspicious" stroke="#d97706" fill="#fffbeb" name="Suspicious" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">Risk Distribution</div>
          </div>
          {riskPieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={riskPieData} cx="50%" cy="50%" innerRadius={55} outerRadius={90}
                  dataKey="value" paddingAngle={2}>
                  {riskPieData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state"><p>No risk data</p></div>
          )}
          <div className="network-legend" style={{ justifyContent: 'center' }}>
            <div className="legend-item"><div className="legend-dot" style={{ background: '#059669' }} /> Safe</div>
            <div className="legend-item"><div className="legend-dot" style={{ background: '#d97706' }} /> Suspicious</div>
            <div className="legend-item"><div className="legend-dot" style={{ background: '#dc2626' }} /> High Risk</div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div className="card-title">Recent Alerts</div>
            <button className="btn btn-sm btn-ghost" onClick={() => navigate('/alerts')}>View all →</button>
          </div>
          {recent_alerts.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Amount</th>
                  <th>Probability</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {recent_alerts.map((a) => (
                  <tr key={a.id}>
                    <td><StatusBadge status={a.severity} /></td>
                    <td>₹{a.amount?.toFixed(2)}</td>
                    <td><ProbabilityBar value={a.fraud_probability} /></td>
                    <td><StatusBadge status={a.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state"><p>No recent alerts</p></div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">High Risk Transactions</div>
            <button className="btn btn-sm btn-ghost" onClick={() => navigate('/transactions')}>View all →</button>
          </div>
          {high_risk_transactions.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>Amount</th>
                  <th>Risk</th>
                  <th>Probability</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {high_risk_transactions.map((t) => (
                  <tr key={t.id} className="clickable" onClick={() => navigate(`/transactions/${t.id}`)}>
                    <td>₹{t.amount?.toFixed(2)}</td>
                    <td><RiskBadge level={t.risk_level} /></td>
                    <td><ProbabilityBar value={t.fraud_probability} /></td>
                    <td><StatusBadge status={t.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state"><p>No high risk transactions</p></div>
          )}
        </div>
      </div>
    </div>
  );
}
