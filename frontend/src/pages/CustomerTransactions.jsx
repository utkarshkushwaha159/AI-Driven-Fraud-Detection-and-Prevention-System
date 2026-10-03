import { useState, useEffect } from 'react';
import { getTransactions } from '../services/api';
import { StatusBadge, LoadingState, EmptyState } from '../components/SharedComponents';

export default function CustomerTransactions({ user }) {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const accountId = user?.account_id || 'ACC-1001';

  useEffect(() => {
    loadTransactions();
  }, [accountId]);

  const loadTransactions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getTransactions({ account_id: accountId, page_size: 50 });
      setTransactions(res.data.transactions || res.data.items || []);
    } catch (err) {
      setError('Failed to load transaction history.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container" style={{ maxWidth: 1000, margin: '0 auto' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>My Transaction History</h1>
          <p>Account statement and status for Account: <strong>{accountId}</strong></p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadTransactions}>
          Refresh
        </button>
      </div>

      {loading && <LoadingState message="Fetching your statement..." />}

      {error && (
        <div className="card" style={{ background: 'var(--color-danger-bg)', color: 'var(--color-danger)', padding: 16 }}>
          {error}
        </div>
      )}

      {!loading && !error && transactions.length === 0 && (
        <EmptyState
          title="No Transactions Found"
          message="You have not initiated any payments from this account yet."
        />
      )}

      {!loading && transactions.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="table">
            <thead>
              <tr>
                <th>Date & Time</th>
                <th>Transaction ID</th>
                <th>Description / Merchant</th>
                <th>Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => (
                <tr key={tx.id}>
                  <td style={{ fontSize: 13, color: 'var(--color-text-secondary)', whiteSpace: 'nowrap' }}>
                    {new Date(tx.created_at).toLocaleString()}
                  </td>
                  <td style={{ fontFamily: 'monospace', fontSize: 12 }}>
                    {tx.id.substring(0, 13)}...
                  </td>
                  <td>
                    <div style={{ fontWeight: 500 }}>
                      {tx.merchant?.name || tx.merchant_id || 'Retail Merchant'}
                    </div>
                    {tx.description && (
                      <div style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>
                        {tx.description}
                      </div>
                    )}
                  </td>
                  <td style={{ fontWeight: 600 }}>
                    ₹{Number(tx.amount).toFixed(2)}
                  </td>
                  <td>
                    <StatusBadge status={tx.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
