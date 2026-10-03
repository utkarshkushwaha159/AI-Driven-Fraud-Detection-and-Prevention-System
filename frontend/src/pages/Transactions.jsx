import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTransactions } from '../services/api';
import { StatusBadge, RiskBadge, ProbabilityBar, LoadingState, EmptyState } from '../components/SharedComponents';

export default function Transactions() {
  const [data, setData] = useState({ transactions: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const pageSize = 20;
  const navigate = useNavigate();

  useEffect(() => { load(); }, [page, statusFilter]);

  const load = async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize, status: statusFilter !== 'all' ? statusFilter : undefined };
      if (search) params.search = search;
      const res = await getTransactions(params);
      setData(res.data);
    } catch { }
    setLoading(false);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    load();
  };

  const totalPages = Math.ceil(data.total / pageSize);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Transactions</h1>
        <p>View and search all processed transactions</p>
      </div>

      <div className="card">
        <div className="filter-bar">
          <form onSubmit={handleSearch} style={{ display: 'flex', flex: 1, gap: 8 }}>
            <input className="form-input search-input" placeholder="Search by ID, account..."
              value={search} onChange={(e) => setSearch(e.target.value)} />
            <button className="btn btn-secondary btn-sm" type="submit">Search</button>
          </form>
          <select className="form-select" style={{ width: 160 }}
            value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
            <option value="all">All Status</option>
            <option value="approved">Approved</option>
            <option value="suspicious">Suspicious</option>
            <option value="held">Held</option>
            <option value="blocked">Blocked</option>
          </select>
        </div>

        {loading ? <LoadingState /> : data.transactions.length === 0 ? (
          <EmptyState title="No transactions" message="No transactions match your criteria." />
        ) : (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Transaction ID</th>
                    <th>Amount</th>
                    <th>Account</th>
                    <th>Status</th>
                    <th>Risk</th>
                    <th>Fraud Prob.</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {data.transactions.map((tx) => (
                    <tr key={tx.id} className="clickable" onClick={() => navigate(`/transactions/${tx.id}`)}>
                      <td><span className="truncate" title={tx.id}>{tx.id.slice(0, 8)}...</span></td>
                      <td style={{ fontWeight: 600 }}>₹{tx.amount?.toFixed(2)}</td>
                      <td><span className="truncate" title={tx.account_id}>...{tx.account_id?.slice(-6)}</span></td>
                      <td><StatusBadge status={tx.status} /></td>
                      <td>{tx.risk_level ? <RiskBadge level={tx.risk_level} /> : '—'}</td>
                      <td>{tx.fraud_probability != null ? <ProbabilityBar value={tx.fraud_probability} /> : '—'}</td>
                      <td className="text-muted text-sm">
                        {tx.created_at ? new Date(tx.created_at).toLocaleDateString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination">
              <span>Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, data.total)} of {data.total}</span>
              <div className="pagination-buttons">
                <button className="btn btn-sm btn-secondary" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
                  Previous
                </button>
                <button className="btn btn-sm btn-secondary" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
