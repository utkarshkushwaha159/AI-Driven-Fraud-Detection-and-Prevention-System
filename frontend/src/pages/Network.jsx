import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { getTransactionNetwork, getFullNetwork, getTransactions } from '../services/api';
import { LoadingState, EmptyState } from '../components/SharedComponents';

const NODE_COLORS = {
  transaction: '#2563eb',
  account: '#059669',
  device: '#7c3aed',
  ip: '#d97706',
  merchant: '#dc2626',
};

const NODE_LABELS = {
  transaction: 'Transaction',
  account: 'Account',
  device: 'Device',
  ip: 'IP Address',
  merchant: 'Merchant',
};

export default function Network() {
  const [searchParams] = useSearchParams();
  const txIdParam = searchParams.get('tx');
  const [networkData, setNetworkData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const [txId, setTxId] = useState(txIdParam || '');
  const [recentTxs, setRecentTxs] = useState([]);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    loadRecentTransactions();
    if (txIdParam) loadNetwork(txIdParam);
    else loadFullNetwork();
  }, [txIdParam]);

  const loadRecentTransactions = async () => {
    try {
      const res = await getTransactions({ page: 1, page_size: 10, status: 'held' });
      if (res.data.transactions.length === 0) {
        const res2 = await getTransactions({ page: 1, page_size: 10 });
        setRecentTxs(res2.data.transactions);
      } else {
        setRecentTxs(res.data.transactions);
      }
    } catch { }
  };

  const loadNetwork = async (id) => {
    setLoading(true);
    try {
      const res = await getTransactionNetwork(id);
      setNetworkData(res.data);
      buildGraph(res.data);
    } catch { }
    setLoading(false);
  };

  const loadFullNetwork = async () => {
    setLoading(true);
    try {
      const res = await getFullNetwork(50);
      setNetworkData(res.data);
      buildGraph(res.data);
    } catch { }
    setLoading(false);
  };

  const buildGraph = (data) => {
    if (!data?.nodes) return;

    const flowNodes = data.nodes.map((n, i) => {
      const angle = (2 * Math.PI * i) / data.nodes.length;
      const radius = 200 + Math.random() * 100;
      return {
        id: n.id,
        position: { x: 400 + radius * Math.cos(angle), y: 300 + radius * Math.sin(angle) },
        data: {
          label: n.label,
          ...n,
        },
        style: {
          background: NODE_COLORS[n.type] || '#666',
          color: '#fff',
          borderRadius: n.type === 'transaction' ? '4px' : '50%',
          width: n.type === 'transaction' ? 100 : 60,
          height: n.type === 'transaction' ? 36 : 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 10,
          fontWeight: 600,
          border: n.risk_score > 0.5 ? '3px solid #dc2626' : '2px solid rgba(255,255,255,0.3)',
          padding: 4,
          textAlign: 'center',
          wordBreak: 'break-all',
        },
      };
    });

    const flowEdges = data.edges.map((e, i) => ({
      id: `e-${i}`,
      source: e.source,
      target: e.target,
      label: e.label || '',
      style: { stroke: '#94a3b8', strokeWidth: 1 },
      labelStyle: { fontSize: 9, fill: '#6b7280' },
      animated: false,
    }));

    setNodes(flowNodes);
    setEdges(flowEdges);
  };

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node.data);
  }, []);

  const handleLoadTx = () => {
    if (txId.trim()) loadNetwork(txId.trim());
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Fraud Network</h1>
        <p>Visualize entity relationships and connections</p>
      </div>

      <div className="filter-bar">
        <input className="form-input" style={{ maxWidth: 340 }}
          value={txId} onChange={(e) => setTxId(e.target.value)}
          placeholder="Enter transaction ID..." />
        <button className="btn btn-primary btn-sm" onClick={handleLoadTx}>Load Network</button>
        <button className="btn btn-secondary btn-sm" onClick={loadFullNetwork}>Overview</button>
        {recentTxs.length > 0 && (
          <select className="form-select" style={{ width: 240 }}
            onChange={(e) => { setTxId(e.target.value); if (e.target.value) loadNetwork(e.target.value); }}>
            <option value="">Select a flagged transaction...</option>
            {recentTxs.map((t) => (
              <option key={t.id} value={t.id}>
                ₹{t.amount?.toFixed(0)} - {t.status} ({t.id.slice(0, 8)})
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="network-legend">
        {Object.entries(NODE_LABELS).map(([type, label]) => (
          <div key={type} className="legend-item">
            <div className="legend-dot" style={{ background: NODE_COLORS[type] }} />
            {label}
          </div>
        ))}
      </div>

      {loading ? <LoadingState message="Building network..." /> : (
        <div className="network-container">
          {nodes.length > 0 ? (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              fitView
              minZoom={0.3}
              maxZoom={2}
            >
              <Background gap={20} color="#f0f0f0" />
              <Controls />
              <MiniMap nodeColor={(n) => NODE_COLORS[n.data?.type] || '#666'} />
            </ReactFlow>
          ) : (
            <EmptyState title="No network data" message="Select a transaction to view its network." />
          )}
        </div>
      )}

      {selectedNode && (
        <div className="card" style={{ marginTop: 16 }}>
          <div className="card-title">Selected: {NODE_LABELS[selectedNode.type] || selectedNode.type}</div>
          <div className="detail-grid" style={{ marginTop: 8 }}>
            <div className="detail-item">
              <div className="detail-item-label">Label</div>
              <div className="detail-item-value">{selectedNode.label}</div>
            </div>
            <div className="detail-item">
              <div className="detail-item-label">Type</div>
              <div className="detail-item-value">{NODE_LABELS[selectedNode.type]}</div>
            </div>
            {selectedNode.risk_score > 0 && (
              <div className="detail-item">
                <div className="detail-item-label">Risk Score</div>
                <div className="detail-item-value">{(selectedNode.risk_score * 100).toFixed(1)}%</div>
              </div>
            )}
            {selectedNode.metadata && Object.entries(selectedNode.metadata).map(([k, v]) => (
              <div key={k} className="detail-item">
                <div className="detail-item-label">{k.replace(/_/g, ' ')}</div>
                <div className="detail-item-value">{String(v)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {networkData?.risk_summary && Object.keys(networkData.risk_summary).length > 0 && (
        <div className="card" style={{ marginTop: 16 }}>
          <div className="card-title">Network Analysis</div>
          <div className="detail-grid" style={{ marginTop: 8 }}>
            {Object.entries(networkData.risk_summary).filter(([k]) =>
              !['top_risk_nodes'].includes(k)
            ).map(([k, v]) => (
              <div key={k} className="detail-item">
                <div className="detail-item-label">{k.replace(/_/g, ' ')}</div>
                <div className="detail-item-value">
                  {typeof v === 'number' ? (v % 1 === 0 ? v : v.toFixed(4)) : String(v)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
