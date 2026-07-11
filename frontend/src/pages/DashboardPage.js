import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Receipt, LayoutDashboard, Upload, BarChart3, ShieldCheck,
  MessageSquare, Plug, LogOut, Search, Bell, Settings,
  ChevronDown, TrendingUp, TrendingDown, MoreHorizontal,
  FileText, Download, Filter, Calendar, CheckCircle2,
  AlertTriangle, XCircle, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell, Legend
} from 'recharts';
import '../styles/DashboardPage.css';

const sidebarItems = [
  { icon: Upload, label: 'Upload Receipt', id: 'upload' },
  { icon: LayoutDashboard, label: 'Dashboard', id: 'dashboard', active: true },
  { icon: BarChart3, label: 'Analytics', id: 'analytics' },
  { icon: ShieldCheck, label: 'Validation', id: 'validation' },
  { icon: MessageSquare, label: 'Chat', id: 'chat' },
  { icon: Plug, label: 'ERP & API', id: 'erp' },
];

const spendingData = [
  { name: 'Mon', amount: 4200 },
  { name: 'Tue', amount: 6800 },
  { name: 'Wed', amount: 5100 },
  { name: 'Thu', amount: 8900 },
  { name: 'Fri', amount: 6200 },
  { name: 'Sat', amount: 9500 },
  { name: 'Sun', amount: 4800 },
];

const categoryData = [
  { name: 'Travel', value: 38, color: '#8B5CF6' },
  { name: 'Food', value: 24, color: '#E879F9' },
  { name: 'Utility', value: 18, color: '#22D3EE' },
  { name: 'Office', value: 12, color: '#FBBF24' },
  { name: 'Other', value: 8, color: '#34D399' },
];

const monthlyData = [
  { name: 'Jan', spend: 42000, receipts: 89 },
  { name: 'Feb', spend: 38000, receipts: 76 },
  { name: 'Mar', spend: 55000, receipts: 112 },
  { name: 'Apr', spend: 48000, receipts: 98 },
  { name: 'May', spend: 62000, receipts: 134 },
  { name: 'Jun', spend: 71000, receipts: 156 },
  { name: 'Jul', spend: 84230, receipts: 128 },
];

const recentReceipts = [
  { vendor: 'Cafe Turmeric', amount: 640, date: 'Jul 08', category: 'Food', status: 'validated', tax: 51 },
  { vendor: 'IndiGo Airlines', amount: 5240, date: 'Jul 06', category: 'Travel', status: 'validated', tax: 420 },
  { vendor: 'BESCOM Electricity', amount: 2380, date: 'Jul 02', category: 'Utility', status: 'pending', tax: 190 },
  { vendor: 'Amazon Business', amount: 12500, date: 'Jun 28', category: 'Office', status: 'validated', tax: 2250 },
  { vendor: 'Ola Cabs', amount: 450, date: 'Jun 25', category: 'Travel', status: 'flagged', tax: 36 },
  { vendor: 'Swiggy', amount: 890, date: 'Jun 22', category: 'Food', status: 'validated', tax: 71 },
];

const validationAlerts = [
  { type: 'duplicate', message: 'Possible duplicate: Receipt #1289 matches #1043', severity: 'warning' },
  { type: 'tax', message: 'Tax rate mismatch in BESCOM bill (expected 8%, got 12%)', severity: 'error' },
  { type: 'compliance', message: 'GSTIN verified for Amazon Business', severity: 'success' },
];

const DashboardPage = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [searchQuery, setSearchQuery] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    // Handle file upload logic here
    alert('Files dropped! In production, this would process the receipts.');
  };

  const kpiCards = [
    {
      label: 'Total Spend',
      value: '₹84,230',
      delta: '↑ 12% vs last month',
      deltaPositive: true,
      icon: TrendingUp,
      color: 'var(--neon-violet)'
    },
    {
      label: 'Receipts',
      value: '128',
      delta: '↑ 8 this week',
      deltaPositive: true,
      icon: FileText,
      color: 'var(--neon-cyan)'
    },
    {
      label: 'Tax Paid',
      value: '₹6,738',
      delta: '8% avg rate',
      deltaPositive: true,
      icon: ShieldCheck,
      color: 'var(--neon-emerald)'
    },
    {
      label: 'Pending',
      value: '3',
      delta: '2 require action',
      deltaPositive: false,
      icon: AlertTriangle,
      color: 'var(--neon-amber)'
    },
  ];

  return (
    <div className="dashboard-page">
      {/* Sidebar */}
      <aside className={`dashboard-sidebar ${sidebarOpen ? 'open' : 'collapsed'}`}>
        <div className="sidebar-header">
          <div className="logo-mark-small">
            <Receipt size={20} color="#fff" strokeWidth={1.8} />
          </div>
          {sidebarOpen && (
            <span className="sidebar-brand">
              Receipt<span className="gradient-text">Vault</span>
            </span>
          )}
        </div>

        <nav className="sidebar-nav">
          {sidebarItems.map((item) => (
            <button
              key={item.id}
              className={`sidebar-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => {
                setActiveTab(item.id);
                if (item.id === 'upload') setShowUploadModal(true);
              }}
            >
              <item.icon size={20} />
              {sidebarOpen && <span>{item.label}</span>}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          {sidebarOpen && (
            <div className="spending-goal">
              <div className="goal-label">SPENDING GOAL</div>
              <div className="goal-value">₹12,450 / ₹50,000</div>
              <div className="goal-bar">
                <div className="goal-fill" style={{ width: '24.9%' }} />
              </div>
            </div>
          )}
          <button className="sidebar-item logout">
            <LogOut size={20} />
            {sidebarOpen && <span>Logout</span>}
          </button>
        </div>

        <button
          className="sidebar-toggle"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          {sidebarOpen ? '◀' : '▶'}
        </button>
      </aside>

      {/* Main Content */}
      <main className="dashboard-main">
        {/* Top Header */}
        <header className="dashboard-header">
          <div className="header-search">
            <Search size={18} className="search-icon" />
            <input
              type="text"
              placeholder="Search receipts, vendors, amounts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="header-actions">
            <button className="header-btn">
              <Bell size={20} />
              <span className="badge">3</span>
            </button>
            <button className="header-btn">
              <Settings size={20} />
            </button>
            <div className="user-profile">
              <div className="user-avatar">RK</div>
              <div className="user-info hide-mobile">
                <div className="user-name">Rahul Kumar</div>
                <div className="user-role">CFO</div>
              </div>
              <ChevronDown size={16} />
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <div className="dashboard-content">
          {/* KPI Row */}
          <div className="kpi-grid">
            {kpiCards.map((kpi, i) => (
              <div key={i} className="kpi-card">
                <div className="kpi-top" style={{ '--accent': kpi.color }}>
                  <div className="kpi-icon" style={{ background: `${kpi.color}20`, color: kpi.color }}>
                    <kpi.icon size={20} />
                  </div>
                  <MoreHorizontal size={16} className="kpi-more" />
                </div>
                <div className="kpi-label">{kpi.label}</div>
                <div className="kpi-value">{kpi.value}</div>
                <div className={`kpi-delta ${kpi.deltaPositive ? 'positive' : 'negative'}`}>
                  {kpi.delta}
                </div>
              </div>
            ))}
          </div>

          {/* Charts Row */}
          <div className="charts-grid">
            <div className="chart-card large">
              <div className="chart-header">
                <h3>Spending Trend</h3>
                <div className="chart-filters">
                  <button className="filter-btn active">7 Days</button>
                  <button className="filter-btn">30 Days</button>
                  <button className="filter-btn">90 Days</button>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={monthlyData}>
                  <defs>
                    <linearGradient id="colorSpend" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" stroke="#64748B" fontSize={12} />
                  <YAxis stroke="#64748B" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      background: '#1A1A3E',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '12px',
                      color: '#F8FAFC'
                    }}
                  />
                  <Area type="monotone" dataKey="spend" stroke="#8B5CF6" strokeWidth={2} fill="url(#colorSpend)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <div className="chart-header">
                <h3>Category Split</h3>
              </div>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: '#1A1A3E',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '12px',
                      color: '#F8FAFC'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="category-legend">
                {categoryData.map((cat, i) => (
                  <div key={i} className="legend-item">
                    <span className="legend-dot" style={{ background: cat.color }} />
                    <span className="legend-name">{cat.name}</span>
                    <span className="legend-value">{cat.value}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Bottom Row */}
          <div className="bottom-grid">
            {/* Recent Receipts */}
            <div className="panel-card">
              <div className="panel-header">
                <h3>Recent Receipts</h3>
                <button className="panel-action">View All</button>
              </div>
              <div className="receipt-list">
                {recentReceipts.map((receipt, i) => (
                  <div key={i} className="receipt-item">
                    <div className="receipt-info">
                      <div className="receipt-vendor">{receipt.vendor}</div>
                      <div className="receipt-meta">
                        <span>{receipt.date}</span>
                        <span>•</span>
                        <span>{receipt.category}</span>
                        <span>•</span>
                        <span>Tax: ₹{receipt.tax}</span>
                      </div>
                    </div>
                    <div className="receipt-right">
                      <div className="receipt-amount">₹{receipt.amount.toLocaleString()}</div>
                      <div className={`receipt-status ${receipt.status}`}>
                        {receipt.status === 'validated' && <CheckCircle2 size={14} />}
                        {receipt.status === 'pending' && <AlertTriangle size={14} />}
                        {receipt.status === 'flagged' && <XCircle size={14} />}
                        {receipt.status}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Validation Alerts */}
            <div className="panel-card">
              <div className="panel-header">
                <h3>Validation Alerts</h3>
                <button className="panel-action">Clear All</button>
              </div>
              <div className="alert-list">
                {validationAlerts.map((alert, i) => (
                  <div key={i} className={`alert-item ${alert.severity}`}>
                    <div className="alert-icon">
                      {alert.severity === 'success' && <CheckCircle2 size={18} />}
                      {alert.severity === 'warning' && <AlertTriangle size={18} />}
                      {alert.severity === 'error' && <XCircle size={18} />}
                    </div>
                    <div className="alert-content">
                      <div className="alert-type">{alert.type}</div>
                      <div className="alert-message">{alert.message}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="panel-card">
              <div className="panel-header">
                <h3>Quick Actions</h3>
              </div>
              <div className="quick-actions">
                <button className="quick-action" onClick={() => setShowUploadModal(true)}>
                  <div className="qa-icon" style={{ background: 'rgba(139,92,246,0.2)', color: '#8B5CF6' }}>
                    <Upload size={20} />
                  </div>
                  <span>Upload Receipt</span>
                  <ArrowUpRight size={16} />
                </button>
                <button className="quick-action">
                  <div className="qa-icon" style={{ background: 'rgba(34,211,238,0.2)', color: '#22D3EE' }}>
                    <Download size={20} />
                  </div>
                  <span>Export Report</span>
                  <ArrowUpRight size={16} />
                </button>
                <button className="quick-action">
                  <div className="qa-icon" style={{ background: 'rgba(52,211,153,0.2)', color: '#34D399' }}>
                    <Filter size={20} />
                  </div>
                  <span>Filter & Search</span>
                  <ArrowUpRight size={16} />
                </button>
                <button className="quick-action">
                  <div className="qa-icon" style={{ background: 'rgba(251,191,36,0.2)', color: '#FBBF24' }}>
                    <Calendar size={20} />
                  </div>
                  <span>Monthly Review</span>
                  <ArrowUpRight size={16} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="modal-overlay" onClick={() => setShowUploadModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Upload Receipts</h3>
              <button className="modal-close" onClick={() => setShowUploadModal(false)}>✕</button>
            </div>
            <div
              className={`upload-dropzone ${dragActive ? 'active' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <Upload size={48} className="upload-icon" />
              <p className="upload-title">Drag & drop your receipts here</p>
              <p className="upload-sub">or click to browse (PNG, JPG, PDF)</p>
              <button className="btn btn-primary upload-btn">Select Files</button>
            </div>
            <div className="upload-formats">
              <span>Supported: PNG, JPG, JPEG, PDF</span>
              <span>Max size: 10MB per file</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
