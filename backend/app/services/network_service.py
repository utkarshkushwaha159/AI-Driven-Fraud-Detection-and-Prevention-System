"""
Network analysis service for fraud detection.
Builds and analyzes relationship graphs between entities.
Uses graph algorithms from the DSA module internally.
"""
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.transaction import Transaction
from app.models.account import Account
from app.models.device import Device
from app.models.ip_address import IpAddress
from app.models.merchant import Merchant
from app.models.model_prediction import ModelPrediction
from app.dsa.graph import Graph
from app.dsa.trees import AVLTree, MaxHeap


class NetworkService:
    """Builds and analyzes fraud relationship networks."""

    @staticmethod
    def build_transaction_network(db: Session, transaction_id: str, depth: int = 2) -> dict:
        """
        Build a network graph around a transaction.
        Returns nodes and edges for visualization.
        """
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            return {"nodes": [], "edges": [], "clusters": [], "risk_summary": {}}

        graph = Graph()
        nodes_data = {}
        edges_data = []

        # Add the center transaction
        tx_risk = 0.0
        if tx.prediction:
            tx_risk = tx.prediction.fraud_probability

        tx_node_id = f"tx_{tx.id[:8]}"
        graph.add_node(tx_node_id, {
            "type": "transaction",
            "label": f"₹{tx.amount:.2f}",
            "risk": tx_risk,
            "full_id": tx.id,
        })
        nodes_data[tx_node_id] = {
            "id": tx_node_id,
            "label": f"₹{tx.amount:.2f}",
            "type": "transaction",
            "risk_score": tx_risk,
            "metadata": {
                "amount": tx.amount,
                "status": tx.status,
                "transaction_id": tx.id,
            }
        }

        # Add account node
        acct_node_id = f"acct_{tx.account_id[:8]}"
        graph.add_node(acct_node_id, {"type": "account", "id": tx.account_id})
        nodes_data[acct_node_id] = {
            "id": acct_node_id,
            "label": f"Account ...{tx.account_id[-6:]}",
            "type": "account",
            "risk_score": 0,
            "metadata": {"account_id": tx.account_id}
        }
        graph.add_edge(acct_node_id, tx_node_id, 1.0, {"relation": "made"})
        edges_data.append({"source": acct_node_id, "target": tx_node_id, "label": "made", "weight": 1.0})

        # Add device node
        if tx.device_id and tx.device:
            dev_node_id = f"dev_{tx.device_id[:8]}"
            graph.add_node(dev_node_id, {"type": "device", "id": tx.device_id})
            nodes_data[dev_node_id] = {
                "id": dev_node_id,
                "label": f"Device ...{tx.device.device_fingerprint[-6:]}",
                "type": "device",
                "risk_score": 0,
                "metadata": {
                    "device_type": tx.device.device_type,
                    "fingerprint": tx.device.device_fingerprint,
                }
            }
            graph.add_edge(tx_node_id, dev_node_id, 1.0, {"relation": "used_device"})
            edges_data.append({"source": tx_node_id, "target": dev_node_id, "label": "used device", "weight": 1.0})

            # Find other accounts using same device
            if depth >= 1:
                other_txs = db.query(Transaction).filter(
                    Transaction.device_id == tx.device_id,
                    Transaction.account_id != tx.account_id
                ).limit(10).all()

                for otx in other_txs:
                    other_acct_id = f"acct_{otx.account_id[:8]}"
                    if other_acct_id not in nodes_data:
                        graph.add_node(other_acct_id, {"type": "account", "id": otx.account_id})
                        nodes_data[other_acct_id] = {
                            "id": other_acct_id,
                            "label": f"Account ...{otx.account_id[-6:]}",
                            "type": "account",
                            "risk_score": 0,
                            "metadata": {"account_id": otx.account_id, "shared_device": True}
                        }
                    graph.add_edge(other_acct_id, dev_node_id, 0.8, {"relation": "shared_device"})
                    edges_data.append({"source": other_acct_id, "target": dev_node_id,
                                      "label": "shared device", "weight": 0.8})

        # Add IP node
        if tx.ip_id and tx.ip_address:
            ip_node_id = f"ip_{tx.ip_id[:8]}"
            graph.add_node(ip_node_id, {"type": "ip", "id": tx.ip_id})
            nodes_data[ip_node_id] = {
                "id": ip_node_id,
                "label": tx.ip_address.ip,
                "type": "ip",
                "risk_score": 0,
                "metadata": {
                    "ip": tx.ip_address.ip,
                    "country": tx.ip_address.country,
                }
            }
            graph.add_edge(tx_node_id, ip_node_id, 1.0, {"relation": "from_ip"})
            edges_data.append({"source": tx_node_id, "target": ip_node_id, "label": "from IP", "weight": 1.0})

            # Find other accounts using same IP
            if depth >= 1:
                other_txs = db.query(Transaction).filter(
                    Transaction.ip_id == tx.ip_id,
                    Transaction.account_id != tx.account_id
                ).limit(10).all()

                for otx in other_txs:
                    other_acct_id = f"acct_{otx.account_id[:8]}"
                    if other_acct_id not in nodes_data:
                        graph.add_node(other_acct_id, {"type": "account", "id": otx.account_id})
                        nodes_data[other_acct_id] = {
                            "id": other_acct_id,
                            "label": f"Account ...{otx.account_id[-6:]}",
                            "type": "account",
                            "risk_score": 0,
                            "metadata": {"account_id": otx.account_id, "shared_ip": True}
                        }
                    graph.add_edge(other_acct_id, ip_node_id, 0.8, {"relation": "shared_ip"})
                    edges_data.append({"source": other_acct_id, "target": ip_node_id,
                                      "label": "shared IP", "weight": 0.8})

        # Add merchant node
        if tx.merchant_id and tx.merchant:
            mer_node_id = f"mer_{tx.merchant_id[:8]}"
            graph.add_node(mer_node_id, {"type": "merchant", "id": tx.merchant_id})
            nodes_data[mer_node_id] = {
                "id": mer_node_id,
                "label": tx.merchant.name,
                "type": "merchant",
                "risk_score": 0,
                "metadata": {
                    "merchant_code": tx.merchant.merchant_code,
                    "category": tx.merchant.category,
                }
            }
            graph.add_edge(tx_node_id, mer_node_id, 1.0, {"relation": "at_merchant"})
            edges_data.append({"source": tx_node_id, "target": mer_node_id,
                              "label": "at merchant", "weight": 1.0})

        # Analyze the graph
        components = graph.connected_components()
        clusters = []
        for i, comp in enumerate(components):
            clusters.append({
                "id": i,
                "size": len(comp),
                "nodes": list(comp),
            })

        # Compute risk summary using graph structure
        risk_summary = NetworkService._compute_network_risk(graph, nodes_data, tx_node_id)

        return {
            "nodes": list(nodes_data.values()),
            "edges": edges_data,
            "clusters": clusters,
            "risk_summary": risk_summary,
        }

    @staticmethod
    def _compute_network_risk(graph, nodes_data, center_node_id):
        """Compute network-level risk indicators using graph analysis."""
        # Use BFS to find network extent
        bfs_order, parents = graph.bfs(center_node_id)

        # Count entity types
        type_counts = defaultdict(int)
        for node_id in bfs_order:
            if node_id in nodes_data:
                type_counts[nodes_data[node_id]["type"]] += 1

        # Shared entities indicate higher risk
        shared_devices = type_counts.get("device", 0)
        shared_ips = type_counts.get("ip", 0)
        connected_accounts = type_counts.get("account", 0)

        # Use MaxHeap to track highest risk nodes
        risk_heap = MaxHeap()
        for node_id, data in nodes_data.items():
            risk_heap.insert(data.get("risk_score", 0), node_id)

        top_risks = risk_heap.get_top_n(3)

        # Network exposure score based on connectivity
        total_nodes = graph.node_count()
        total_edges = graph.edge_count()
        center_degree = graph.degree(center_node_id)

        network_exposure = min(1.0, (total_nodes * 0.1 + total_edges * 0.05 + center_degree * 0.15))

        return {
            "total_entities": total_nodes,
            "total_connections": total_edges,
            "connected_accounts": connected_accounts,
            "shared_devices": shared_devices,
            "shared_ips": shared_ips,
            "network_exposure": round(network_exposure, 4),
            "cluster_count": len(graph.connected_components()),
            "top_risk_nodes": [{"node": n, "risk": r} for r, n in top_risks],
        }

    @staticmethod
    def get_full_network(db: Session, limit: int = 200) -> dict:
        """Build a broader network view from recent transactions."""
        transactions = db.query(Transaction).order_by(
            Transaction.created_at.desc()
        ).limit(limit).all()

        graph = Graph()
        nodes_data = {}
        edges_data = []
        seen_edges = set()

        for tx in transactions:
            acct_id = f"acct_{tx.account_id[:8]}"
            if acct_id not in nodes_data:
                risk = tx.prediction.fraud_probability if tx.prediction else 0
                graph.add_node(acct_id, {"type": "account"})
                nodes_data[acct_id] = {
                    "id": acct_id, "label": f"...{tx.account_id[-6:]}",
                    "type": "account", "risk_score": risk, "metadata": {}
                }

            if tx.device_id:
                dev_id = f"dev_{tx.device_id[:8]}"
                if dev_id not in nodes_data:
                    graph.add_node(dev_id, {"type": "device"})
                    fp = tx.device.device_fingerprint if tx.device else tx.device_id[:8]
                    nodes_data[dev_id] = {
                        "id": dev_id, "label": f"...{fp[-6:]}",
                        "type": "device", "risk_score": 0, "metadata": {}
                    }
                edge_key = (acct_id, dev_id)
                if edge_key not in seen_edges:
                    graph.add_edge(acct_id, dev_id)
                    edges_data.append({"source": acct_id, "target": dev_id, "label": "", "weight": 1})
                    seen_edges.add(edge_key)

            if tx.ip_id:
                ip_id = f"ip_{tx.ip_id[:8]}"
                if ip_id not in nodes_data:
                    ip_label = tx.ip_address.ip if tx.ip_address else tx.ip_id[:8]
                    graph.add_node(ip_id, {"type": "ip"})
                    nodes_data[ip_id] = {
                        "id": ip_id, "label": ip_label,
                        "type": "ip", "risk_score": 0, "metadata": {}
                    }
                edge_key = (acct_id, ip_id)
                if edge_key not in seen_edges:
                    graph.add_edge(acct_id, ip_id)
                    edges_data.append({"source": acct_id, "target": ip_id, "label": "", "weight": 1})
                    seen_edges.add(edge_key)

        # Find connected components for clustering
        components = graph.connected_components()
        clusters = [{"id": i, "size": len(c), "nodes": list(c)} for i, c in enumerate(components)]

        return {
            "nodes": list(nodes_data.values()),
            "edges": edges_data,
            "clusters": clusters,
            "risk_summary": {"total_entities": len(nodes_data), "total_connections": len(edges_data)},
        }
