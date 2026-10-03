import { useState } from 'react';
import { checkPayment } from '../services/api';

export default function CustomerPayment({ user }) {
  const [formData, setFormData] = useState({
    account_id: user?.account_id || 'ACC-1001',
    amount: '1250.00',
    merchant_code: 'AMZN_US',
    description: 'Online purchase - Electronics',
    device_fingerprint: 'DEV-DESKTOP-CHROME-01',
    ip_address: '192.168.1.45',
    device_type: 'desktop',
    os_name: 'Windows 11',
    browser: 'Chrome 122',
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [otpStep, setOtpStep] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [otpSuccess, setOtpSuccess] = useState(false);

  const merchants = [
    { code: 'AMZN_US', name: 'Amazon US - Marketplace' },
    { code: 'APPL_STORE', name: 'Apple Store Retail' },
    { code: 'STRIPE_MCH', name: 'Digital Services Merchant' },
    { code: 'WMT_RETAIL', name: 'Walmart Supercenter' },
    { code: 'CRYPTO_EX', name: 'Apex Digital Exchange (High Volume)' },
  ];

  const presets = [
    {
      title: 'Safe Transaction',
      subtitle: '₹450.00 everyday purchase from trusted device',
      amount: '450.00',
      merchant_code: 'WMT_RETAIL',
      description: 'Household groceries',
      device_fingerprint: 'DEV-DESKTOP-CHROME-01',
      ip_address: '192.168.1.45',
    },
    {
      title: 'Suspicious Transaction',
      subtitle: '₹45,000.00 electronics purchase from new device',
      amount: '45000.00',
      merchant_code: 'APPL_STORE',
      description: 'MacBook Air - express delivery',
      device_fingerprint: 'DEV-UNKNOWN-NEW-8821',
      ip_address: '198.51.100.99',
    },
    {
      title: 'High-Risk Transaction',
      subtitle: '₹2,50,000.00 wire to crypto exchange from proxy IP',
      amount: '250000.00',
      merchant_code: 'CRYPTO_EX',
      description: 'Instant crypto wallet top-up',
      device_fingerprint: 'DEV-PROXY-EMULATOR-009',
      ip_address: '203.0.113.195',
    },
  ];

  const handlePreset = (preset) => {
    setFormData((prev) => ({
      ...prev,
      amount: preset.amount,
      merchant_code: preset.merchant_code,
      description: preset.description,
      device_fingerprint: preset.device_fingerprint,
      ip_address: preset.ip_address,
    }));
    setResult(null);
    setError(null);
    setOtpStep(false);
    setOtpSuccess(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setOtpStep(false);
    setOtpSuccess(false);

    try {
      const payload = {
        account_id: formData.account_id || user?.account_id || 'ACC-1001',
        amount: parseFloat(formData.amount),
        merchant_code: formData.merchant_code,
        description: formData.description,
        device_fingerprint: formData.device_fingerprint,
        ip_address: formData.ip_address,
        device_type: formData.device_type,
        os_name: formData.os_name,
        browser: formData.browser,
      };

      const res = await checkPayment(payload);
      setResult(res.data);
      if (res.data.status === 'suspicious') {
        setOtpStep(true);
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Payment processing failed. Please check backend connection.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = (e) => {
    e.preventDefault();
    if (otpCode.length === 6) {
      setOtpSuccess(true);
      setOtpStep(false);
    } else {
      alert('Please enter a valid 6-digit verification code (e.g. 123456)');
    }
  };

  return (
    <div className="page-container" style={{ maxWidth: 860, margin: '0 auto' }}>
      <div className="page-header">
        <h1>Secure Payment Portal</h1>
        <p>Customer checkout with real-time multi-layered security screening</p>
      </div>

      <div style={{ marginBottom: 20 }}>
        <label className="form-label" style={{ fontWeight: 600, color: 'var(--color-navy)' }}>
          Quick Simulation Presets:
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12, marginTop: 8 }}>
          {presets.map((p, idx) => (
            <button
              key={idx}
              type="button"
              className="btn btn-secondary"
              onClick={() => handlePreset(p)}
              style={{
                textAlign: 'left',
                padding: '12px 14px',
                height: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: 4,
              }}
            >
              <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--color-primary)' }}>
                {p.title}
              </div>
              <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', lineHeight: 1.3 }}>
                {p.subtitle}
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="form-group">
              <label className="form-label">Account ID</label>
              <input
                type="text"
                className="form-control"
                value={formData.account_id}
                onChange={(e) => setFormData({ ...formData, account_id: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Amount (INR ₹)</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                className="form-control"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                required
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="form-group">
              <label className="form-label">Merchant</label>
              <select
                className="form-control"
                value={formData.merchant_code}
                onChange={(e) => setFormData({ ...formData, merchant_code: e.target.value })}
              >
                {merchants.map((m) => (
                  <option key={m.code} value={m.code}>
                    {m.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Description / Purpose</label>
              <input
                type="text"
                className="form-control"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="form-group">
              <label className="form-label">Device Fingerprint</label>
              <input
                type="text"
                className="form-control"
                value={formData.device_fingerprint}
                onChange={(e) => setFormData({ ...formData, device_fingerprint: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">IP Address</label>
              <input
                type="text"
                className="form-control"
                value={formData.ip_address}
                onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
              />
            </div>
          </div>

          <div style={{ marginTop: 12, display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ minWidth: 160 }}
            >
              {loading ? 'Screening Payment...' : 'Check & Pay'}
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div
          className="card"
          style={{
            background: 'var(--color-danger-bg)',
            borderColor: 'var(--color-danger)',
            padding: 16,
            marginBottom: 20,
          }}
        >
          <div style={{ color: 'var(--color-danger)', fontWeight: 600 }}>Security Error</div>
          <div style={{ color: 'var(--color-text)', fontSize: 13, marginTop: 4 }}>{error}</div>
        </div>
      )}

      {result && (
        <div
          className="card"
          style={{
            borderLeft: `4px solid ${
              result.status === 'approved'
                ? 'var(--color-success)'
                : result.status === 'suspicious'
                ? 'var(--color-warning)'
                : 'var(--color-danger)'
            }`,
            background:
              result.status === 'approved'
                ? 'var(--color-success-bg)'
                : result.status === 'suspicious'
                ? 'var(--color-warning-bg)'
                : 'var(--color-danger-bg)',
            padding: 24,
            marginBottom: 24,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h2
                style={{
                  fontSize: 18,
                  fontWeight: 600,
                  color:
                    result.status === 'approved'
                      ? 'var(--color-success)'
                      : result.status === 'suspicious'
                      ? 'var(--color-warning)'
                      : 'var(--color-danger)',
                }}
              >
                {result.status === 'approved' && 'Payment Approved'}
                {result.status === 'suspicious' && 'Additional Verification Required'}
                {result.status === 'held' && 'Transaction Held for Security Review'}
              </h2>
              <p style={{ marginTop: 6, fontSize: 14, color: 'var(--color-text)' }}>
                {result.message}
              </p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>Amount</div>
              <div style={{ fontSize: 20, fontWeight: 700 }}>
                ₹{Number(result.amount).toFixed(2)}
              </div>
            </div>
          </div>

          <div
            style={{
              marginTop: 16,
              paddingTop: 14,
              borderTop: '1px solid rgba(0,0,0,0.08)',
              display: 'flex',
              gap: 24,
              fontSize: 12,
              color: 'var(--color-text-secondary)',
            }}
          >
            <div>
              <strong>Transaction ID:</strong> <span style={{ fontFamily: 'monospace' }}>{result.transaction_id}</span>
            </div>
            <div>
              <strong>Status:</strong>{' '}
              <span className={`badge badge-${result.status}`}>
                {result.status.toUpperCase()}
              </span>
            </div>
          </div>

          {otpStep && !otpSuccess && (
            <div
              style={{
                marginTop: 20,
                padding: 16,
                background: '#fff',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--color-border)',
              }}
            >
              <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>
                Simulate Two-Factor Authentication (OTP)
              </h3>
              <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 12 }}>
                Enter verification code sent to registered mobile/email (use <code>123456</code> to simulate approval):
              </p>
              <form onSubmit={handleVerifyOtp} style={{ display: 'flex', gap: 10, maxWidth: 300 }}>
                <input
                  type="text"
                  maxLength={6}
                  placeholder="123456"
                  className="form-control"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value)}
                  style={{ textAlign: 'center', letterSpacing: 4, fontWeight: 600 }}
                />
                <button type="submit" className="btn btn-primary">
                  Verify
                </button>
              </form>
            </div>
          )}

          {otpSuccess && (
            <div
              style={{
                marginTop: 16,
                padding: 14,
                background: 'var(--color-success-bg)',
                color: 'var(--color-success)',
                borderRadius: 'var(--radius-md)',
                fontWeight: 600,
                fontSize: 13,
              }}
            >
              ✓ Verification Successful. Payment has been released and confirmed.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
