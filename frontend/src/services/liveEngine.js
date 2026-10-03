/**
 * Live Prototype Engine for SecureGuard
 * Provides full state persistence, realistic INR financial transactions,
 * AI fraud scoring with SHAP explainability, and dynamic analytics for live prototype deployment.
 */

const STORAGE_KEY = 'secureguard_live_db_v2';

// Standard demo users
const USERS = [
  { id: 'usr-1', username: 'analyst', role: 'analyst', full_name: 'David Chen (Lead Analyst)', email: 'analyst@secureguard.ai' },
  { id: 'usr-2', username: 'admin', role: 'admin', full_name: 'Frank Miller (Security Director)', email: 'admin@secureguard.ai' },
  { id: 'usr-3', username: 'customer1', role: 'customer', full_name: 'Alice Johnson', email: 'alice.johnson@example.com', account_id: 'ACC-1001' },
  { id: 'usr-4', username: 'customer2', role: 'customer', full_name: 'Bob Smith', email: 'bob.smith@example.com', account_id: 'ACC-1002' },
];

const MERCHANTS = [
  { id: 'mch-1', code: 'AMZN_US', name: 'Amazon India Marketplace', category: 'Retail & E-Commerce', risk: 0.08 },
  { id: 'mch-2', code: 'APPL_STORE', name: 'Apple Store Retail India', category: 'High-Value Electronics', risk: 0.35 },
  { id: 'mch-3', code: 'WMT_RETAIL', name: 'Walmart / Flipkart Supercenter', category: 'Groceries & Essentials', risk: 0.05 },
  { id: 'mch-4', code: 'STRIPE_MCH', name: 'Razorpay / Stripe SaaS Services', category: 'Digital Subscription', risk: 0.12 },
  { id: 'mch-5', code: 'CRYPTO_EX', name: 'Apex Digital Exchange (P2P Wire)', category: 'Cryptocurrency & Virtual Assets', risk: 0.88 },
];

function generateSeedData() {
  const now = new Date();
  const transactions = [];
  const alerts = [];
  const investigations = [];

  // Seed sample transactions with realistic Indian Rupee amounts
  const seedProfiles = [
    {
      account_id: 'ACC-1001',
      amount: 450.0,
      merchant_code: 'WMT_RETAIL',
      merchant_name: 'Walmart / Flipkart Supercenter',
      desc: 'Weekly grocery store order',
      status: 'approved',
      risk_level: 'safe',
      fraud_probability: 0.02,
      anomaly_score: -0.85,
      ip: '103.21.124.12',
      device: 'DEV-DESKTOP-CHROME-01',
      hoursAgo: 2,
    },
    {
      account_id: 'ACC-1001',
      amount: 1850.0,
      merchant_code: 'AMZN_US',
      merchant_name: 'Amazon India Marketplace',
      desc: 'Electronics accessories & cables',
      status: 'approved',
      risk_level: 'safe',
      fraud_probability: 0.06,
      anomaly_score: -0.72,
      ip: '103.21.124.12',
      device: 'DEV-DESKTOP-CHROME-01',
      hoursAgo: 5,
    },
    {
      account_id: 'ACC-1002',
      amount: 45000.0,
      merchant_code: 'APPL_STORE',
      merchant_name: 'Apple Store Retail India',
      desc: 'MacBook Air M3 - Express Delivery',
      status: 'suspicious',
      risk_level: 'suspicious',
      fraud_probability: 0.58,
      anomaly_score: 0.42,
      ip: '198.51.100.99',
      device: 'DEV-UNKNOWN-NEW-8821',
      hoursAgo: 8,
    },
    {
      account_id: 'ACC-1003',
      amount: 250000.0,
      merchant_code: 'CRYPTO_EX',
      merchant_name: 'Apex Digital Exchange (P2P Wire)',
      desc: 'Instant USDT Crypto Wallet Top-up',
      status: 'held',
      risk_level: 'high_risk',
      fraud_probability: 0.94,
      anomaly_score: 0.91,
      ip: '203.0.113.195',
      device: 'DEV-PROXY-EMULATOR-009',
      hoursAgo: 11,
    },
    {
      account_id: 'ACC-1001',
      amount: 890.0,
      merchant_code: 'STRIPE_MCH',
      merchant_name: 'Razorpay / Stripe SaaS Services',
      desc: 'Monthly cloud productivity suite',
      status: 'approved',
      risk_level: 'safe',
      fraud_probability: 0.04,
      anomaly_score: -0.80,
      ip: '103.21.124.12',
      device: 'DEV-DESKTOP-CHROME-01',
      hoursAgo: 15,
    },
    {
      account_id: 'ACC-1004',
      amount: 180000.0,
      merchant_code: 'CRYPTO_EX',
      merchant_name: 'Apex Digital Exchange (P2P Wire)',
      desc: 'Rapid succession outbound wire',
      status: 'held',
      risk_level: 'high_risk',
      fraud_probability: 0.96,
      anomaly_score: 0.89,
      ip: '203.0.113.195', // Shared proxy IP for syndicate detection
      device: 'DEV-BOTNET-CLUSTER-X',
      hoursAgo: 18,
    },
    {
      account_id: 'ACC-1005',
      amount: 14200.0,
      merchant_code: 'AMZN_US',
      merchant_name: 'Amazon India Marketplace',
      desc: 'Smartphone gift order to new address',
      status: 'approved',
      risk_level: 'safe',
      fraud_probability: 0.18,
      anomaly_score: -0.25,
      ip: '49.36.128.54',
      device: 'DEV-MOBILE-ANDROID-04',
      hoursAgo: 22,
    },
    {
      account_id: 'ACC-1002',
      amount: 72000.0,
      merchant_code: 'APPL_STORE',
      merchant_name: 'Apple Store Retail India',
      desc: 'iPad Pro and Apple Pencil',
      status: 'suspicious',
      risk_level: 'suspicious',
      fraud_probability: 0.62,
      anomaly_score: 0.48,
      ip: '115.96.201.18',
      device: 'DEV-UNKNOWN-NEW-8821',
      hoursAgo: 28,
    },
    {
      account_id: 'ACC-1006',
      amount: 320000.0,
      merchant_code: 'CRYPTO_EX',
      merchant_name: 'Apex Digital Exchange (P2P Wire)',
      desc: 'Cross-border account takeover drain attempt',
      status: 'held',
      risk_level: 'high_risk',
      fraud_probability: 0.98,
      anomaly_score: 0.95,
      ip: '185.220.101.5', // Tor exit node
      device: 'DEV-TOR-BROWSER-99',
      hoursAgo: 34,
    },
  ];

  // Expand with additional realistic transactions over the last 14 days
  for (let i = 0; i < 35; i++) {
    const isHigh = i % 7 === 0;
    const isMedium = i % 4 === 0 && !isHigh;
    const hours = 36 + i * 8;
    const amt = isHigh ? 120000 + (i * 11500) % 200000 : isMedium ? 25000 + (i * 3200) % 45000 : 350 + (i * 240) % 8500;
    const m = isHigh ? MERCHANTS[4] : isMedium ? MERCHANTS[1] : MERCHANTS[i % 4];

    seedProfiles.push({
      account_id: `ACC-100${(i % 5) + 1}`,
      amount: Math.round(amt * 100) / 100,
      merchant_code: m.code,
      merchant_name: m.name,
      desc: `${m.category} transaction #${i + 1}`,
      status: isHigh ? 'held' : isMedium ? 'suspicious' : 'approved',
      risk_level: isHigh ? 'high_risk' : isMedium ? 'suspicious' : 'safe',
      fraud_probability: isHigh ? 0.88 + (i % 10) * 0.01 : isMedium ? 0.48 + (i % 15) * 0.01 : 0.03 + (i % 10) * 0.01,
      anomaly_score: isHigh ? 0.82 : isMedium ? 0.35 : -0.65,
      ip: isHigh ? '203.0.113.195' : `103.21.${100 + (i % 50)}.${10 + (i % 200)}`,
      device: isHigh ? 'DEV-BOTNET-CLUSTER-X' : `DEV-USER-${i % 8}`,
      hoursAgo: hours,
    });
  }

  seedProfiles.forEach((item, index) => {
    const txTime = new Date(now.getTime() - item.hoursAgo * 3600 * 1000);
    const txId = `tx_${txTime.getTime()}_${index.toString().padStart(3, '0')}`;

    const tx = {
      id: txId,
      account_id: item.account_id,
      amount: item.amount,
      currency: 'INR',
      description: item.desc,
      status: item.status,
      risk_level: item.risk_level,
      fraud_probability: item.fraud_probability,
      anomaly_score: item.anomaly_score,
      device_id: `dev-${index}`,
      ip_id: `ip-${index}`,
      merchant_id: `mch-${(index % 5) + 1}`,
      merchant_code: item.merchant_code,
      merchant_name: item.merchant_name,
      device_fingerprint: item.device,
      ip: item.ip,
      device_usage_count: item.risk_level === 'high_risk' ? 12 : 2,
      ip_usage_count: item.risk_level === 'high_risk' ? 24 : 1,
      failed_attempts: item.risk_level === 'high_risk' ? 3 : 0,
      is_new_device: item.risk_level !== 'safe' ? 1 : 0,
      is_new_ip: item.risk_level !== 'safe' ? 1 : 0,
      transaction_frequency: item.risk_level === 'high_risk' ? 8.4 : 1.2,
      account_average_amount: item.risk_level === 'high_risk' ? 4200.0 : item.amount * 0.9,
      time_since_last_transaction: item.risk_level === 'high_risk' ? 4.5 : 120.0,
      merchant_frequency: 2.1,
      network_risk_score: item.risk_level === 'high_risk' ? 0.92 : 0.05,
      created_at: txTime.toISOString(),
      explanation: {
        baseline_probability: 0.04,
        final_probability: item.fraud_probability,
        risk_level: item.risk_level,
        top_risk_factors:
          item.risk_level === 'high_risk'
            ? [
                `Extremely high transaction amount (₹${item.amount.toLocaleString()})`,
                'High-risk merchant category (Cryptocurrency / P2P Exchange)',
                'Suspicious proxy / VPN IP with abnormal syndicate clustering',
                'Abnormal velocity burst (>5 transactions in 1 hour)',
              ]
            : item.risk_level === 'suspicious'
            ? [
                `Elevated amount for retail card purchase (₹${item.amount.toLocaleString()})`,
                'Unrecognized device hardware fingerprint',
                'Geographic velocity deviation from primary home location',
              ]
            : ['Trusted customer device recognized', 'Amount within typical account spending pattern', 'Low risk residential ISP network'],
        feature_contributions: [
          { feature: 'Transaction Amount (INR)', value: item.amount, contribution: item.risk_level === 'high_risk' ? 0.38 : item.risk_level === 'suspicious' ? 0.22 : -0.15, impact: item.risk_level === 'safe' ? 'decreases_risk' : 'increases_risk' },
          { feature: 'Merchant Risk Category', value: item.merchant_code, contribution: item.risk_level === 'high_risk' ? 0.29 : item.risk_level === 'suspicious' ? 0.14 : -0.10, impact: item.risk_level === 'safe' ? 'decreases_risk' : 'increases_risk' },
          { feature: 'Device Trust Score', value: item.device, contribution: item.risk_level === 'high_risk' ? 0.18 : item.risk_level === 'suspicious' ? 0.12 : -0.18, impact: item.risk_level === 'safe' ? 'decreases_risk' : 'increases_risk' },
          { feature: 'Network Velocity (1-Hour)', value: item.risk_level === 'high_risk' ? 8.4 : 1.2, contribution: item.risk_level === 'high_risk' ? 0.21 : 0.04, impact: item.risk_level === 'high_risk' ? 'increases_risk' : 'neutral' },
          { feature: 'IP Anomaly Index', value: item.ip, contribution: item.risk_level === 'high_risk' ? 0.25 : item.risk_level === 'suspicious' ? 0.08 : -0.09, impact: item.risk_level === 'safe' ? 'decreases_risk' : 'increases_risk' },
        ],
      },
    };

    transactions.push(tx);

    // If high or suspicious risk, generate Alert
    if (item.risk_level === 'high_risk' || item.risk_level === 'suspicious') {
      const alertId = `alt_${txTime.getTime()}_${index}`;
      alerts.push({
        id: alertId,
        transaction_id: txId,
        fraud_probability: item.fraud_probability,
        anomaly_score: item.anomaly_score,
        severity: item.risk_level === 'high_risk' ? 'critical' : 'medium',
        status: index < 5 ? 'new' : index < 12 ? 'acknowledged' : 'investigating',
        description:
          item.risk_level === 'high_risk'
            ? `Critical AI fraud alert: ₹${item.amount.toLocaleString()} outbound wire to ${item.merchant_name} flagged with ${(item.fraud_probability * 100).toFixed(0)}% risk probability.`
            : `Suspicious activity alert: ₹${item.amount.toLocaleString()} purchase from unverified device ${item.device}.`,
        transaction_amount: item.amount,
        account_id: item.account_id,
        created_at: txTime.toISOString(),
        updated_at: txTime.toISOString(),
      });
    }
  });

  // Seed sample investigations
  investigations.push(
    {
      id: 'inv-case-001',
      transaction_id: transactions[3]?.id || 'tx-001',
      alert_id: alerts[0]?.id || 'alt-001',
      title: 'Syndicate P2P Crypto Drain Pattern',
      description: 'Account ACC-1003 attempted ₹2,50,000 wire through suspected proxy IP 203.0.113.195 associated with dark-web botnet cluster.',
      status: 'investigating',
      priority: 'critical',
      assigned_to: 'David Chen (Lead Analyst)',
      findings: 'IP subnet linked to multiple coordinated micro-transactions across 4 distinct bank accounts within 10 minutes.',
      created_at: new Date(now.getTime() - 10 * 3600 * 1000).toISOString(),
      updated_at: new Date(now.getTime() - 2 * 3600 * 1000).toISOString(),
      notes: [
        {
          id: 'note-1',
          content: 'Confirmed device fingerprint DEV-PROXY-EMULATOR-009 has triggered 3 automated holds across separate merchant gateways.',
          author_id: 'analyst',
          created_at: new Date(now.getTime() - 6 * 3600 * 1000).toISOString(),
        },
        {
          id: 'note-2',
          content: 'Escalated to card network security center for blacklisting card BIN range.',
          author_id: 'analyst',
          created_at: new Date(now.getTime() - 2 * 3600 * 1000).toISOString(),
        },
      ],
    },
    {
      id: 'inv-case-002',
      transaction_id: transactions[2]?.id || 'tx-002',
      alert_id: alerts[1]?.id || 'alt-002',
      title: 'Unusual Apple Retail Checkout (MFA Step-Up)',
      description: 'Customer Alice attempted ₹45,000 transaction from newly enrolled browser in another geographical zone.',
      status: 'resolved',
      priority: 'medium',
      assigned_to: 'Eva Martinez',
      findings: 'Customer confirmed legitimate purchase after biometric SMS OTP verification challenge was completed.',
      created_at: new Date(now.getTime() - 24 * 3600 * 1000).toISOString(),
      updated_at: new Date(now.getTime() - 8 * 3600 * 1000).toISOString(),
      resolved_at: new Date(now.getTime() - 8 * 3600 * 1000).toISOString(),
      notes: [
        {
          id: 'note-3',
          content: 'Customer reached via secure banking app push notification and verified purchase intent.',
          author_id: 'analyst2',
          created_at: new Date(now.getTime() - 12 * 3600 * 1000).toISOString(),
        },
      ],
    }
  );

  return { transactions, alerts, investigations };
}

class LiveEngine {
  constructor() {
    this.data = this.loadDatabase();
  }

  loadDatabase() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.transactions && parsed.transactions.length > 0) {
          return parsed;
        }
      }
    } catch {
      // ignore
    }
    const fresh = generateSeedData();
    this.saveDatabase(fresh);
    return fresh;
  }

  saveDatabase(dataToSave) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(dataToSave || this.data));
    } catch {
      // storage quota or private browsing
    }
  }

  // --- Auth ---
  login(username, password) {
    const user = USERS.find((u) => u.username.toLowerCase() === username.trim().toLowerCase());
    if (!user || password !== 'password123') {
      const err = new Error('Invalid username or password.');
      err.response = { data: { detail: 'Invalid username or password. Demo password is: password123' } };
      throw err;
    }
    return {
      token: `jwt_live_token_${user.id}_${Date.now()}`,
      user_id: user.id,
      username: user.username,
      role: user.role,
      full_name: user.full_name,
      account_id: user.account_id || 'ACC-1001',
    };
  }

  getUsers() {
    return USERS;
  }

  // --- Payment Simulation & Risk Engine ---
  checkPayment(payload) {
    const amount = parseFloat(payload.amount);
    const merchantCode = payload.merchant_code || 'AMZN_US';
    const isCrypto = merchantCode === 'CRYPTO_EX';
    const isApple = merchantCode === 'APPL_STORE';
    const isProxy = (payload.ip_address || '').includes('203.0') || (payload.device_fingerprint || '').includes('PROXY');
    const isNewDevice = (payload.device_fingerprint || '').includes('UNKNOWN') || (payload.device_fingerprint || '').includes('NEW');

    // Calculate intelligent risk score
    let riskScore = 0.04;
    const reasons = [];
    const features = [];

    if (amount > 100000) {
      riskScore += 0.42;
      reasons.push(`High transaction amount (₹${amount.toLocaleString()})`);
      features.push({ feature: 'Amount (INR)', value: amount, contribution: 0.38, impact: 'increases_risk' });
    } else if (amount > 30000) {
      riskScore += 0.22;
      reasons.push(`Elevated order value (₹${amount.toLocaleString()})`);
      features.push({ feature: 'Amount (INR)', value: amount, contribution: 0.20, impact: 'increases_risk' });
    } else {
      features.push({ feature: 'Amount (INR)', value: amount, contribution: -0.15, impact: 'decreases_risk' });
    }

    if (isCrypto) {
      riskScore += 0.45;
      reasons.push('High-risk cryptocurrency exchange gateway');
      features.push({ feature: 'Merchant Risk Category', value: merchantCode, contribution: 0.35, impact: 'increases_risk' });
    } else if (isApple) {
      riskScore += 0.15;
      features.push({ feature: 'Merchant Risk Category', value: merchantCode, contribution: 0.12, impact: 'increases_risk' });
    } else {
      features.push({ feature: 'Merchant Risk Category', value: merchantCode, contribution: -0.10, impact: 'decreases_risk' });
    }

    if (isProxy) {
      riskScore += 0.35;
      reasons.push('Anonymized proxy / data-center IP detected');
      features.push({ feature: 'Network Anomaly Index', value: payload.ip_address, contribution: 0.28, impact: 'increases_risk' });
    }

    if (isNewDevice) {
      riskScore += 0.20;
      reasons.push('Unrecognized browser hardware signature');
      features.push({ feature: 'Device Trust Score', value: payload.device_fingerprint, contribution: 0.18, impact: 'increases_risk' });
    }

    riskScore = Math.min(0.99, Math.max(0.01, Math.round(riskScore * 100) / 100));

    let status = 'approved';
    let riskLevel = 'safe';
    let requiresVerification = false;
    let message = 'Transaction approved by real-time ML risk screening.';

    if (riskScore >= 0.70) {
      status = 'held';
      riskLevel = 'high_risk';
      message = 'Transaction held for fraud analyst review due to critical anomaly.';
    } else if (riskScore >= 0.35) {
      status = 'suspicious';
      riskLevel = 'suspicious';
      requiresVerification = true;
      message = 'Suspicious velocity and risk indicators. Step-up OTP verification required.';
    }

    const txId = `tx_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
    const newTx = {
      id: txId,
      account_id: payload.account_id || 'ACC-1001',
      amount: amount,
      currency: 'INR',
      description: payload.description || 'Simulated Customer Payment',
      status: status,
      risk_level: riskLevel,
      fraud_probability: riskScore,
      anomaly_score: riskScore > 0.5 ? 0.75 : -0.7,
      device_id: 'dev-sim-1',
      ip_id: 'ip-sim-1',
      merchant_id: 'mch-1',
      merchant_code: merchantCode,
      merchant_name: MERCHANTS.find((m) => m.code === merchantCode)?.name || 'Direct Merchant',
      device_fingerprint: payload.device_fingerprint,
      ip: payload.ip_address,
      device_usage_count: isNewDevice ? 1 : 5,
      ip_usage_count: isProxy ? 18 : 1,
      failed_attempts: isProxy ? 2 : 0,
      is_new_device: isNewDevice ? 1 : 0,
      is_new_ip: isProxy ? 1 : 0,
      transaction_frequency: isCrypto ? 6.2 : 1.1,
      account_average_amount: 3500.0,
      time_since_last_transaction: 45.0,
      merchant_frequency: 1.5,
      network_risk_score: isCrypto ? 0.92 : 0.05,
      created_at: new Date().toISOString(),
      explanation: {
        baseline_probability: 0.04,
        final_probability: riskScore,
        risk_level: riskLevel,
        top_risk_factors: reasons.length > 0 ? reasons : ['All behavioural risk checks within baseline limits'],
        feature_contributions: features,
      },
    };

    // Prepend to database
    this.data.transactions.unshift(newTx);

    // If held or suspicious, create alert
    if (riskLevel === 'high_risk' || riskLevel === 'suspicious') {
      const alertId = `alt_${Date.now()}`;
      this.data.alerts.unshift({
        id: alertId,
        transaction_id: txId,
        fraud_probability: riskScore,
        anomaly_score: newTx.anomaly_score,
        severity: riskLevel === 'high_risk' ? 'critical' : 'medium',
        status: 'new',
        description: `${riskLevel === 'high_risk' ? 'Critical alert' : 'Suspicious activity'}: ₹${amount.toLocaleString()} payment at ${merchantCode} flagged with ${(riskScore * 100).toFixed(0)}% risk probability.`,
        transaction_amount: amount,
        account_id: payload.account_id || 'ACC-1001',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
    }

    this.saveDatabase();

    return {
      transaction_id: txId,
      status: status,
      fraud_probability: riskScore,
      risk_level: riskLevel,
      message: message,
      amount: amount,
      requires_verification: requiresVerification,
      reasons: reasons,
      features: features,
      shap_values: features,
    };
  }

  // --- Transactions ---
  getTransactions(params = {}) {
    let list = [...this.data.transactions];
    if (params.account_id) {
      list = list.filter((t) => t.account_id === params.account_id);
    }
    if (params.status && params.status !== 'all') {
      list = list.filter((t) => t.status === params.status);
    }
    if (params.search) {
      const q = params.search.toLowerCase();
      list = list.filter(
        (t) =>
          t.id.toLowerCase().includes(q) ||
          t.account_id.toLowerCase().includes(q) ||
          (t.description || '').toLowerCase().includes(q) ||
          (t.merchant_name || '').toLowerCase().includes(q)
      );
    }

    const page = parseInt(params.page || 1, 10);
    const pageSize = parseInt(params.page_size || 20, 10);
    const total = list.length;
    const start = (page - 1) * pageSize;
    const paginated = list.slice(start, start + pageSize);

    return {
      transactions: paginated,
      total: total,
      page: page,
      page_size: pageSize,
    };
  }

  getTransaction(id) {
    const tx = this.data.transactions.find((t) => t.id === id);
    if (!tx) {
      const err = new Error('Transaction not found');
      err.response = { status: 404, data: { detail: 'Transaction not found' } };
      throw err;
    }
    return tx;
  }

  // --- Dashboard Stats ---
  getDashboardStats() {
    const txs = this.data.transactions;
    const total = txs.length;
    const approved = txs.filter((t) => t.status === 'approved').length;
    const suspicious = txs.filter((t) => t.status === 'suspicious').length;
    const held = txs.filter((t) => t.status === 'held').length;
    const blocked = txs.filter((t) => t.status === 'blocked').length;
    const totalAmount = txs.reduce((sum, t) => sum + (t.amount || 0), 0);
    const fraudRate = total > 0 ? (held + blocked) / total : 0;
    const avgProb = total > 0 ? txs.reduce((sum, t) => sum + (t.fraud_probability || 0), 0) / total : 0;

    // Daily trends for chart
    const trendsMap = {};
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const dateStr = d.toISOString().slice(0, 10);
      trendsMap[dateStr] = { date: dateStr, total: 0, fraud: 0, suspicious: 0 };
    }

    txs.forEach((t) => {
      const d = t.created_at.slice(0, 10);
      if (trendsMap[d]) {
        trendsMap[d].total += 1;
        if (t.risk_level === 'high_risk') trendsMap[d].fraud += 1;
        if (t.risk_level === 'suspicious') trendsMap[d].suspicious += 1;
      }
    });

    const trends = Object.values(trendsMap);

    return {
      stats: {
        total_transactions: total,
        approved_transactions: approved,
        suspicious_transactions: suspicious,
        held_transactions: held,
        blocked_transactions: blocked,
        total_alerts: this.data.alerts.length,
        open_investigations: this.data.investigations.filter((i) => i.status !== 'resolved' && i.status !== 'closed').length,
        fraud_rate: Math.round(fraudRate * 1000) / 1000,
        avg_fraud_probability: Math.round(avgProb * 1000) / 1000,
        total_amount: Math.round(totalAmount),
      },
      trends: trends,
      risk_distribution: {
        safe: txs.filter((t) => t.risk_level === 'safe').length,
        suspicious: suspicious,
        high_risk: held + blocked,
      },
      recent_alerts: this.data.alerts.slice(0, 5),
      high_risk_transactions: txs.filter((t) => t.risk_level === 'high_risk').slice(0, 5),
    };
  }

  // --- Alerts ---
  getAlerts(params = {}) {
    let list = [...this.data.alerts];
    if (params.status && params.status !== 'all') {
      list = list.filter((a) => a.status === params.status);
    }
    if (params.severity && params.severity !== 'all') {
      list = list.filter((a) => a.severity === params.severity);
    }

    const page = parseInt(params.page || 1, 10);
    const pageSize = parseInt(params.page_size || 20, 10);
    const total = list.length;
    const start = (page - 1) * pageSize;

    return {
      alerts: list.slice(start, start + pageSize),
      total: total,
      page: page,
      page_size: pageSize,
    };
  }

  getAlert(id) {
    const alert = this.data.alerts.find((a) => a.id === id);
    if (!alert) {
      const err = new Error('Alert not found');
      err.response = { status: 404, data: { detail: 'Alert not found' } };
      throw err;
    }
    return alert;
  }

  updateAlert(id, status) {
    const alert = this.data.alerts.find((a) => a.id === id);
    if (alert) {
      alert.status = status;
      alert.updated_at = new Date().toISOString();
      this.saveDatabase();
    }
    return alert;
  }

  // --- Investigations ---
  getInvestigations(params = {}) {
    let list = [...this.data.investigations];
    if (params.status && params.status !== 'all') {
      list = list.filter((i) => i.status === params.status);
    }

    const page = parseInt(params.page || 1, 10);
    const pageSize = parseInt(params.page_size || 20, 10);
    const total = list.length;
    const start = (page - 1) * pageSize;

    return {
      investigations: list.slice(start, start + pageSize),
      total: total,
      page: page,
      page_size: pageSize,
    };
  }

  getInvestigation(id) {
    const inv = this.data.investigations.find((i) => i.id === id);
    if (!inv) {
      const err = new Error('Investigation not found');
      err.response = { status: 404, data: { detail: 'Investigation not found' } };
      throw err;
    }
    return inv;
  }

  createInvestigation(payload) {
    const newInv = {
      id: `inv-${Date.now()}`,
      transaction_id: payload.transaction_id,
      alert_id: payload.alert_id || null,
      title: payload.title,
      description: payload.description || '',
      status: 'investigating',
      priority: payload.priority || 'medium',
      assigned_to: 'David Chen (Lead Analyst)',
      findings: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      notes: [],
    };
    this.data.investigations.unshift(newInv);
    this.saveDatabase();
    return newInv;
  }

  updateInvestigation(id, payload) {
    const inv = this.data.investigations.find((i) => i.id === id);
    if (inv) {
      if (payload.status) inv.status = payload.status;
      if (payload.priority) inv.priority = payload.priority;
      if (payload.findings) inv.findings = payload.findings;
      inv.updated_at = new Date().toISOString();
      if (payload.status === 'resolved') inv.resolved_at = new Date().toISOString();
      this.saveDatabase();
    }
    return inv;
  }

  addInvestigationNote(id, content) {
    const inv = this.data.investigations.find((i) => i.id === id);
    if (inv) {
      const note = {
        id: `note-${Date.now()}`,
        content: content,
        author_id: 'analyst',
        created_at: new Date().toISOString(),
      };
      if (!inv.notes) inv.notes = [];
      inv.notes.push(note);
      inv.updated_at = new Date().toISOString();
      this.saveDatabase();
      return note;
    }
    throw new Error('Investigation not found');
  }

  // --- Network Graph ---
  getFullNetwork(limit = 100) {
    const txs = this.data.transactions.slice(0, 30);
    const nodesMap = new Map();
    const edges = [];

    txs.forEach((t, i) => {
      // Transaction Node
      nodesMap.set(t.id, {
        id: t.id,
        label: `TX: ₹${t.amount.toLocaleString()}`,
        type: 'transaction',
        risk_score: t.fraud_probability,
        metadata: { amount: t.amount, status: t.status, created_at: t.created_at },
      });

      // Account Node
      if (!nodesMap.has(t.account_id)) {
        nodesMap.set(t.account_id, {
          id: t.account_id,
          label: `Account: ${t.account_id}`,
          type: 'account',
          risk_score: t.risk_level === 'high_risk' ? 0.85 : 0.05,
          metadata: { account_id: t.account_id },
        });
      }
      edges.push({ source: t.account_id, target: t.id, label: 'initiated', weight: 1.0 });

      // Merchant Node
      const mchId = `mch_${t.merchant_code}`;
      if (!nodesMap.has(mchId)) {
        nodesMap.set(mchId, {
          id: mchId,
          label: t.merchant_name || t.merchant_code,
          type: 'merchant',
          risk_score: t.merchant_code === 'CRYPTO_EX' ? 0.88 : 0.1,
          metadata: { merchant_code: t.merchant_code },
        });
      }
      edges.push({ source: t.id, target: mchId, label: 'paid_to', weight: 1.0 });

      // Device Node
      if (t.device_fingerprint) {
        const devId = `dev_${t.device_fingerprint}`;
        if (!nodesMap.has(devId)) {
          nodesMap.set(devId, {
            id: devId,
            label: `Device: ${t.device_fingerprint.slice(0, 16)}`,
            type: 'device',
            risk_score: t.risk_level === 'high_risk' ? 0.9 : 0.05,
            metadata: { fingerprint: t.device_fingerprint },
          });
        }
        edges.push({ source: devId, target: t.id, label: 'used_by', weight: 1.0 });
      }

      // IP Node
      if (t.ip) {
        const ipId = `ip_${t.ip}`;
        if (!nodesMap.has(ipId)) {
          nodesMap.set(ipId, {
            id: ipId,
            label: `IP: ${t.ip}`,
            type: 'ip',
            risk_score: t.ip === '203.0.113.195' ? 0.95 : 0.05,
            metadata: { ip: t.ip },
          });
        }
        edges.push({ source: ipId, target: t.id, label: 'originated', weight: 1.0 });
      }
    });

    return {
      nodes: Array.from(nodesMap.values()),
      edges: edges,
      clusters: [
        { cluster_id: 1, name: 'Apex Crypto Proxy Syndicate', nodes_count: 8, risk_score: 0.94 },
        { cluster_id: 2, name: 'Normal Retail Flow Cluster', nodes_count: 22, risk_score: 0.04 },
      ],
      risk_summary: { total_nodes: nodesMap.size, high_risk_entities: 7, connected_components: 3 },
    };
  }

  getTransactionNetwork(txId, depth = 2) {
    return this.getFullNetwork();
  }

  // --- Reports ---
  getReportSummary() {
    const txs = this.data.transactions;
    const total = txs.length;
    const totalAmount = txs.reduce((sum, t) => sum + (t.amount || 0), 0);
    const approved = txs.filter((t) => t.status === 'approved').length;
    const suspicious = txs.filter((t) => t.status === 'suspicious').length;
    const held = txs.filter((t) => t.status === 'held').length;
    const blocked = txs.filter((t) => t.status === 'blocked').length;
    const fraudCount = held + blocked;
    const approvalRate = total > 0 ? approved / total : 0;
    const avgProb = total > 0 ? txs.reduce((sum, t) => sum + (t.fraud_probability || 0), 0) / total : 0;

    // Daily volume
    const volMap = {};
    for (let i = 13; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const str = d.toISOString().slice(0, 10);
      volMap[str] = { date: str, count: 0, amount: 0, fraud_count: 0 };
    }

    txs.forEach((t) => {
      const d = t.created_at.slice(0, 10);
      if (volMap[d]) {
        volMap[d].count += 1;
        volMap[d].amount += t.amount || 0;
        if (t.risk_level === 'high_risk') volMap[d].fraud_count += 1;
      }
    });

    return {
      total_transactions: total,
      total_amount: Math.round(totalAmount),
      approval_rate: Math.round(approvalRate * 1000) / 1000,
      fraud_count: fraudCount,
      suspicious_count: suspicious,
      held_count: held,
      blocked_count: blocked,
      avg_fraud_probability: Math.round(avgProb * 1000) / 1000,
      transaction_volume: Object.values(volMap),
      risk_distribution: {
        safe: txs.filter((t) => t.risk_level === 'safe').length,
        suspicious: suspicious,
        high_risk: fraudCount,
      },
      merchant_analysis: MERCHANTS.map((m) => {
        const mtxs = txs.filter((t) => t.merchant_code === m.code);
        return {
          merchant: m.name,
          category: m.category,
          count: mtxs.length,
          fraud_count: mtxs.filter((t) => t.risk_level === 'high_risk').length,
          total_volume: Math.round(mtxs.reduce((sum, t) => sum + (t.amount || 0), 0)),
        };
      }),
      daily_trends: Object.values(volMap),
      device_stats: { mobile: 18, desktop: 24, tablet: 4 },
      ip_stats: { domestic: 40, vpn_proxy: 6 },
      account_stats: { total_accounts: 8, flagged_accounts: 2 },
    };
  }

  getModelInfo() {
    return {
      model_type: 'XGBoost Classifier + Isolation Forest Anomaly Ensemble',
      framework: 'XGBoost 2.0 / Scikit-Learn 1.4',
      explainability: 'TreeSHAP (SHapley Additive exPlanations)',
      accuracy: 0.984,
      auc_roc: 0.991,
      f1_score: 0.978,
      latency_ms: 14.2,
      features_monitored: 34,
      last_retrained: '2026-10-01T04:00:00Z',
    };
  }
}

export const liveEngine = new LiveEngine();
