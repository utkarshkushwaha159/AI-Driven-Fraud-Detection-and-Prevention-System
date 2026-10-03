import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getInvestigations, updateInvestigation, addInvestigationNote, adminApprovePayment, adminRejectPayment } from '../services/api';
import { StatusBadge, LoadingState, EmptyState } from '../components/SharedComponents';

export default function Investigations({ user }) {
  const [data, setData] = useState({ investigations: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('all');
  const [selected, setSelected] = useState(null);
  const [newNote, setNewNote] = useState('');
  const [newStatus, setNewStatus] = useState('');
  const [actionMsg, setActionMsg] = useState(null);
  const navigate = useNavigate();
  const pageSize = 20;

  useEffect(() => { load(); }, [page, statusFilter]);

  const load = async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize };
      if (statusFilter !== 'all') params.status = statusFilter;
      const res = await getInvestigations(params);
      setData(res.data);
    } catch { }
    setLoading(false);
  };

  const handleAdminApprove = async () => {
    if (!selected?.transaction_id) return;
    try {
      const res = await adminApprovePayment(selected.transaction_id);
      setActionMsg('✓ Payment approved and released by Administrator.');
      await updateInvestigation(selected.id, { status: 'resolved' });
      load();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to approve payment.');
    }
  };

  const handleAdminReject = async () => {
    if (!selected?.transaction_id) return;
    try {
      const res = await adminRejectPayment(selected.transaction_id);
      setActionMsg('✓ Payment rejected and permanently blocked by Administrator.');
      await updateInvestigation(selected.id, { status: 'closed' });
      load();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to reject payment.');
    }
  };

  const handleUpdateStatus = async (invId, status) => {
    try {
      await updateInvestigation(invId, { status });
      load();
      if (selected?.id === invId) setSelected({ ...selected, status });
    } catch { }
  };

  const handleAddNote = async () => {
    if (!selected || !newNote.trim()) return;
    try {
      await addInvestigationNote(selected.id, newNote.trim());
      setNewNote('');
      // Refresh
      const res = await getInvestigations({ page, page_size: pageSize,
        status: statusFilter !== 'all' ? statusFilter : undefined });
      setData(res.data);
      const updated = res.data.investigations.find(i => i.id === selected.id);
      if (updated) setSelected(updated);
    } catch { }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Investigations</h1>
        <p>Manage fraud investigation cases</p>
      </div>

      <div style={{ display: 'flex', gap: 20 }}>
        <div style={{ flex: 1 }}>
          <div className="card">
            <div className="filter-bar">
              <select className="form-select" style={{ width: 180 }}
                value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
                <option value="all">All Status</option>
                <option value="open">Open</option>
                <option value="under_review">Under Review</option>
                <option value="ready_for_admin_review">Ready for Admin Review</option>
                <option value="escalated">Escalated</option>
                <option value="resolved">Resolved</option>
                <option value="false_positive">False Positive</option>
              </select>
            </div>

            {loading ? <LoadingState /> : data.investigations.length === 0 ? (
              <EmptyState icon="🔍" title="No investigations" message="No investigation cases found." />
            ) : (
              <div>
                {data.investigations.map((inv) => (
                  <div key={inv.id}
                    onClick={() => { setSelected(inv); setNewStatus(inv.status); setActionMsg(null); }}
                    style={{
                      padding: '12px 16px', borderBottom: '1px solid #f0f1f3',
                      cursor: 'pointer', background: selected?.id === inv.id ? '#f8f9fb' : 'transparent',
                    }}>
                    <div className="flex items-center justify-between">
                      <div style={{ fontWeight: 500, fontSize: 13 }}>{inv.title}</div>
                      <StatusBadge status={inv.status} />
                    </div>
                    <div className="flex items-center gap-2" style={{ marginTop: 4, fontSize: 12, color: '#6b7280' }}>
                      <StatusBadge status={inv.priority} />
                      <span>{inv.created_at ? new Date(inv.created_at).toLocaleDateString() : ''}</span>
                      <span>{inv.notes?.length || 0} notes</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {selected && (
          <div style={{ width: 420 }}>
            <div className="card">
              <div className="card-title" style={{ marginBottom: 12 }}>{selected.title}</div>
              <div className="detail-grid">
                <div className="detail-item">
                  <div className="detail-item-label">Status</div>
                  <div className="detail-item-value"><StatusBadge status={selected.status} /></div>
                </div>
                <div className="detail-item">
                  <div className="detail-item-label">Priority</div>
                  <div className="detail-item-value"><StatusBadge status={selected.priority} /></div>
                </div>
              </div>

              {selected.description && (
                <p style={{ fontSize: 13, color: '#6b7280', marginTop: 12 }}>{selected.description}</p>
              )}

              {actionMsg && (
                <div style={{ marginTop: 12, padding: 10, background: 'var(--color-success-bg)', color: 'var(--color-success)', borderRadius: 4, fontSize: 13, fontWeight: 500 }}>
                  {actionMsg}
                </div>
              )}

              <div style={{ marginTop: 16 }}>
                <div className="form-group">
                  <label className="form-label">Update Status</label>
                  <div className="flex gap-2">
                    <select className="form-select" style={{ flex: 1 }}
                      value={newStatus} onChange={(e) => setNewStatus(e.target.value)}>
                      <option value="open">Open</option>
                      <option value="under_review">Under Review</option>
                      <option value="ready_for_admin_review">Ready for Admin Review</option>
                      <option value="escalated">Escalated</option>
                      <option value="resolved">Resolved</option>
                      <option value="false_positive">False Positive</option>
                    </select>
                    <button className="btn btn-sm btn-primary"
                      onClick={() => handleUpdateStatus(selected.id, newStatus)}>Update</button>
                  </div>
                </div>
              </div>

              {user?.role === 'analyst' && selected.status !== 'ready_for_admin_review' && selected.status !== 'resolved' && (
                <div style={{ marginTop: 8 }}>
                  <button
                    className="btn btn-sm btn-secondary"
                    style={{ width: '100%', borderColor: 'var(--color-primary)', color: 'var(--color-primary)' }}
                    onClick={() => handleUpdateStatus(selected.id, 'ready_for_admin_review')}
                  >
                    ✓ Mark Ready for Admin Review
                  </button>
                </div>
              )}

              {user?.role === 'admin' && (
                <div style={{ marginTop: 16, padding: 14, borderRadius: 6, background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8, color: 'var(--color-navy)' }}>
                    🛡️ Admin Final Decision
                  </div>
                  <div style={{ display: 'flex', gap: 10 }}>
                    <button
                      className="btn btn-sm"
                      style={{ background: '#10b981', color: '#fff', border: 'none', flex: 1, padding: '8px 12px', fontWeight: 600 }}
                      onClick={handleAdminApprove}
                    >
                      Approve Payment
                    </button>
                    <button
                      className="btn btn-sm btn-danger"
                      style={{ flex: 1, padding: '8px 12px', fontWeight: 600 }}
                      onClick={handleAdminReject}
                    >
                      Reject & Block
                    </button>
                  </div>
                </div>
              )}

              <div className="flex gap-2" style={{ marginTop: 12 }}>
                <button className="btn btn-sm btn-secondary"
                  onClick={() => navigate(`/transactions/${selected.transaction_id}`)}>
                  View Transaction
                </button>
                <button className="btn btn-sm btn-secondary"
                  onClick={() => navigate(`/network?tx=${selected.transaction_id}`)}>
                  View Network
                </button>
              </div>

              <div style={{ marginTop: 20 }}>
                <div className="card-title" style={{ marginBottom: 12 }}>Notes</div>
                {selected.notes && selected.notes.length > 0 ? (
                  selected.notes.map((note) => (
                    <div key={note.id} className="note-item">
                      <div className="note-content">{note.content}</div>
                      <div className="note-meta">
                        {note.created_at ? new Date(note.created_at).toLocaleString() : ''}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-muted text-sm">No notes yet.</p>
                )}

                <div style={{ marginTop: 12 }}>
                  <textarea className="form-textarea" value={newNote}
                    onChange={(e) => setNewNote(e.target.value)}
                    placeholder="Add a note..." style={{ minHeight: 60 }} />
                  <button className="btn btn-sm btn-primary" style={{ marginTop: 8 }}
                    onClick={handleAddNote} disabled={!newNote.trim()}>
                    Add Note
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
