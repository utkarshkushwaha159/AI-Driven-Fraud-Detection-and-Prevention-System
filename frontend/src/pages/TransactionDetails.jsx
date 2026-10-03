import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getTransaction, getTransactionNetwork, createInvestigation } from '../services/api';
import { StatusBadge, RiskBadge, ProbabilityBar, LoadingState } from '../components/SharedComponents';

export default function TransactionDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [tx, setTx] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateInv, setShowCreateInv] = useState(false);
  const [invTitle, setInvTitle] = useState('');
  const [invDesc, setInvDesc] = useState('');

  useEffect(() => { loadTx(); }, [id]);

  const loadTx = async () => {
    setLoading(true);
    try {
      const res = await getTransaction(id);
      setTx(res.data);
    } catch { }
    setLoading(false);
  };

  const handleCreateInvestigation = async () => {
    try {
      await createInvestigation({
        transaction_id: id,
        title: invTitle || `Investigation for ${id.slice(0, 8)}`,
        description: invDesc,
        priority: tx?.risk_level === 'high_risk' ? 'critical' : 'medium',
      });
      setShowCreateInv(false);
      setInvTitle('');
      setInvDesc('');
      alert('Investigation created successfully.');
    } catch { alert('Failed to create investigation.'); }
  };

  if (loading) return <LoadingState message="Loading transaction..." />;
  if (!tx) return <div className="page-container"><p>Transaction not found.</p></div>;

  const explanation = tx.explanation;

  return (
    <div className="page-container">
      <Link to="/transactions" className="back-link">← Back to Transactions</Link>

      <div className="page-header">
        <div className="flex items-center gap-4">
          <h1>Transaction Details</h1>
          <StatusBadge status={tx.status} />
          {tx.risk_level && <RiskBadge level={tx.risk_level} />}
        </div>
        <p>{tx.id}</p>
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-title" style={{ marginBottom: 12 }}>Transaction Information</div>
          <div className="detail-grid">
            <div className="detail-item">
              <div className="detail-item-label">Amount</div>
              <div className="detail-item-value" style={{ fontSize: 20 }}>₹{tx.amount?.toFixed(2)}</div>
            </div>
            <div className="detail-item">
              <div className="detail-item-label">Date</div>
              <div className="detail-item-value">{tx.created_at ? new Date(tx.created_at).toLocaleString() : '—'}</div>
            </div>
            <div className="detail-item">
              <div className="detail-item-label">Account</div>
              <div className="detail-item-value">{tx.account_id?.slice(0, 12)}...</div>
            </div>
            <div className="detail-item">
              <div className="detail-item-label">Merchant</div>
              <div className="detail-item-value">{tx.merchant_name || tx.merchant_code || '—'}</div>
            </div>
            <div className="detail-item">
              <div className="detail-item-label">Device</div>
              <div className="detail-item-value">{tx.device_fingerprint ? `...${tx.device_fingerprint.slice(-8)}` : '—'}</div>
            </div>
            <div className="detail-item">
              <div className="detail-item-label">IP Address</div>
              <div className="detail-item-value">{tx.ip || '—'}</div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: 12 }}>Risk Analysis</div>
          <div className="detail-grid">
            <div className="detail-item">
              <div className="detail-item-label">Fraud Probability</div>
              <div className="detail-item-value">
                {tx.fraud_probability != null ? <ProbabilityBar value={tx.fraud_probability} /> : '—'}
              </div>
            </div>
            <div className="detail-item">
              <div className="detail-item-label">Anomaly Score</div>
              <div className="detail-item-value">
                {tx.anomaly_score != null ? `${(tx.anomaly_score * 100).toFixed(1)}%` : '—'}
              </div>
            </div>
            <div className="detail-item">
              <div className="detail-item-label">New Device</div>
              <div className="detail-item-value">{tx.is_new_device ? 'Yes' : 'No'}</div>
            </div>
            <div className="detail-item">
              <div className="detail-item-label">New IP</div>
              <div className="detail-item-value">{tx.is_new_ip ? 'Yes' : 'No'}</div>
            </div>
            <div className="detail-item">
              <div className="detail-item-label">Failed Attempts</div>
              <div className="detail-item-value">{tx.failed_attempts || 0}</div>
            </div>
            <div className="detail-item">
              <div className="detail-item-label">Account Average</div>
              <div className="detail-item-value">₹{tx.account_average_amount?.toFixed(2) || '—'}</div>
            </div>
          </div>

          <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
            <button className="btn btn-sm btn-secondary" onClick={() => navigate(`/network?tx=${id}`)}>
              View Network
            </button>
            <button className="btn btn-sm btn-primary" onClick={() => setShowCreateInv(true)}>
              Create Investigation
            </button>
          </div>
        </div>
      </div>

      {explanation && explanation.factors && explanation.factors.length > 0 && (
        <div className="card">
          <div className="card-title" style={{ marginBottom: 12 }}>
            Why was this transaction flagged?
          </div>
          <div className="card-subtitle" style={{ marginBottom: 16 }}>
            Key factors that influenced the risk assessment
          </div>
          <div className="factor-list">
            {explanation.factors.map((f, i) => (
              <div key={i} className={`factor-item ${f.direction}`}>
                <div className="factor-message">{f.message}</div>
                <span className={`factor-impact ${f.impact}`}>
                  {f.impact}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {showCreateInv && (
        <div className="modal-overlay" onClick={() => setShowCreateInv(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Create Investigation</h3>
            <div className="form-group">
              <label className="form-label">Title</label>
              <input className="form-input" value={invTitle} onChange={(e) => setInvTitle(e.target.value)}
                placeholder="Investigation title" />
            </div>
            <div className="form-group">
              <label className="form-label">Description</label>
              <textarea className="form-textarea" value={invDesc} onChange={(e) => setInvDesc(e.target.value)}
                placeholder="Describe the investigation..." />
            </div>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setShowCreateInv(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleCreateInvestigation}>Create</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
