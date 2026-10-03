import { useState, useEffect } from 'react';
import { getReportSummary } from '../services/api';
import { LoadingState, StatCard } from '../components/SharedComponents';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line
} from 'recharts';

const COLORS = ['#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed'];

export default function Reports() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReport();
  }, []);

  const loadReport = async () => {
    try {
      const res = await getReportSummary();
      setData(res.data);
    } catch { }
    setLoading(false);
  };

  if (loading) return <LoadingState message="Generating report..." />;
  if (!data) return <div className="page-container"><p>Failed to load report data.</p></div>;

  const riskPieData = [
    { name: 'Safe', value: data.risk_distribution?.safe || 0 },
    { name: 'Suspicious', value: data.risk_distribution?.suspicious || 0 },
    { name: 'High Risk', value: data.risk_distribution?.high_risk || 0 },
  ].filter(d => d.value > 0);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Reports</h1>
        <p>Comprehensive fraud detection analytics</p>
      </div>

      <div className="stats-grid">
        <StatCard label="Total Transactions" value={data.total_transactions.toLocaleString()} />
        <StatCard label="Total Volume" value={`₹${data.total_amount.toLocaleString()}`} />
        <StatCard label="Approval Rate" value={`${(data.approval_rate * 100).toFixed(1)}%`} />
        <StatCard label="Fraud Count" value={data.fraud_count} />
        <StatCard label="Suspicious" value={data.suspicious_count} />
        <StatCard label="Avg Fraud Prob." value={`${(data.avg_fraud_probability * 100).toFixed(1)}%`} />
      </div>

      <div className="charts-grid">
        <div className="card">
          <div className="card-header">
            <div className="card-title">Transaction Volume (Daily)</div>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.transaction_volume || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(d) => d.slice(5)} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="total" fill="#2563eb" radius={[2, 2, 0, 0]} name="Total" />
              <Bar dataKey="fraud" fill="#dc2626" radius={[2, 2, 0, 0]} name="Held" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">Risk Distribution</div>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={riskPieData} cx="50%" cy="50%" outerRadius={100}
                dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                {riskPieData.map((_, i) => (
                  <Cell key={i} fill={['#059669', '#d97706', '#dc2626'][i]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-title" style={{ marginBottom: 12 }}>Entity Statistics</div>
          <div className="detail-grid">
            <div className="detail-item">
              <div className="detail-item-label">Unique Accounts</div>
              <div className="detail-item-value">{data.account_stats?.unique_accounts || 0}</div>
            </div>
            <div className="detail-item">
              <div className="detail-item-label">Unique Devices</div>
              <div className="detail-item-value">{data.device_stats?.unique_devices || 0}</div>
            </div>
            <div className="detail-item">
              <div className="detail-item-label">Unique IPs</div>
              <div className="detail-item-value">{data.ip_stats?.unique_ips || 0}</div>
            </div>
            <div className="detail-item">
              <div className="detail-item-label">Blocked</div>
              <div className="detail-item-value">{data.blocked_count || 0}</div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: 12 }}>Top Merchants by Activity</div>
          {data.merchant_analysis && data.merchant_analysis.length > 0 ? (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Merchant</th>
                    <th>Transactions</th>
                    <th>Avg Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {data.merchant_analysis.slice(0, 8).map((m, i) => (
                    <tr key={i}>
                      <td className="text-sm">{m.merchant_id?.slice(0, 12) || '—'}</td>
                      <td>{m.transaction_count}</td>
                      <td>₹{m.avg_amount?.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-muted text-sm">No merchant data</p>
          )}
        </div>
      </div>
    </div>
  );
}
