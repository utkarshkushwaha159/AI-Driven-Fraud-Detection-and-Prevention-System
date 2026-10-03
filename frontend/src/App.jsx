import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import TransactionDetails from './pages/TransactionDetails';
import Alerts from './pages/Alerts';
import Investigations from './pages/Investigations';
import Network from './pages/Network';
import Reports from './pages/Reports';
import CustomerPayment from './pages/CustomerPayment';
import CustomerTransactions from './pages/CustomerTransactions';
import AdminPanel from './pages/AdminPanel';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import './index.css';

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem('user');
    if (stored) {
      try { setUser(JSON.parse(stored)); } catch { localStorage.clear(); }
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
    localStorage.setItem('token', userData.token);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.clear();
  };

  if (!user) {
    return (
      <BrowserRouter>
        <Login onLogin={handleLogin} />
      </BrowserRouter>
    );
  }

  const isCustomer = user.role === 'customer';

  if (isCustomer) {
    return (
      <BrowserRouter>
        <div className="customer-layout">
          <Navbar user={user} onLogout={handleLogout} />
          <div className="customer-content">
            <Routes>
              <Route path="/payment" element={<CustomerPayment user={user} />} />
              <Route path="/my-transactions" element={<CustomerTransactions user={user} />} />
              <Route path="*" element={<Navigate to="/payment" />} />
            </Routes>
          </div>
        </div>
      </BrowserRouter>
    );
  }

  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar user={user} onLogout={handleLogout} />
        <div className="app-content">
          <Routes>
            <Route path="/dashboard" element={<Dashboard user={user} />} />
            <Route path="/transactions" element={<Transactions user={user} />} />
            <Route path="/transactions/:id" element={<TransactionDetails user={user} />} />
            <Route path="/alerts" element={<Alerts user={user} />} />
            <Route path="/investigations" element={<Investigations user={user} />} />
            <Route path="/network" element={<Network user={user} />} />
            <Route path="/reports" element={<Reports user={user} />} />
            {user.role === 'admin' && (
              <Route path="/admin-panel" element={<AdminPanel user={user} />} />
            )}
            <Route path="*" element={<Navigate to="/dashboard" />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
