import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Receipt, LayoutDashboard, Upload, BarChart3,
  MessageSquare, Plug, LogOut, Search, Bell, Settings,
  ChevronDown, TrendingUp, TrendingDown, MoreHorizontal,
  FileText, Download, Filter, Calendar, CheckCircle2,
  AlertTriangle, XCircle, ArrowUpRight, ArrowDownRight,
  Sun, Moon
} from 'lucide-react';
import ChatPage from './ChatPage';
import ERPPage from './ERPPage';
import MonthlyExpenseDisplay from '../components/MonthlyExpenseDisplay';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell, Legend, LineChart, Line,
  RadialBarChart, RadialBar, ComposedChart, ReferenceLine
} from 'recharts';
import '../styles/DashboardPage.css';

const sidebarItems = [
  { icon: Upload, label: 'Upload Receipt', id: 'upload' },
  { icon: LayoutDashboard, label: 'Dashboard', id: 'dashboard', active: true },
  { icon: BarChart3, label: 'Analytics', id: 'analytics' },
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
  { name: 'Jan', spend: 42000, receipts: 89, categories: { Travel: 15800, Food: 10080, Utility: 7560, Office: 5040, Other: 3360 }, avgPerReceipt: 472, topVendor: 'IndiGo Airlines', budget: 45000, variance: -7.1 },
  { name: 'Feb', spend: 38000, receipts: 76, categories: { Travel: 14440, Food: 9120, Utility: 6840, Office: 4560, Other: 3040 }, avgPerReceipt: 500, topVendor: 'Cafe Coffee Day', budget: 45000, variance: -18.4 },
  { name: 'Mar', spend: 55000, receipts: 112, categories: { Travel: 20900, Food: 13200, Utility: 9900, Office: 6600, Other: 4400 }, avgPerReceipt: 491, topVendor: 'Amazon Business', budget: 45000, variance: 18.2 },
  { name: 'Apr', spend: 48000, receipts: 98, categories: { Travel: 18240, Food: 11520, Utility: 8640, Office: 5760, Other: 3840 }, avgPerReceipt: 490, topVendor: 'Uber', budget: 50000, variance: -4.0 },
  { name: 'May', spend: 62000, receipts: 134, categories: { Travel: 23560, Food: 14880, Utility: 11160, Office: 7440, Other: 4960 }, avgPerReceipt: 463, topVendor: 'IndiGo Airlines', budget: 55000, variance: 11.3 },
  { name: 'Jun', spend: 71000, receipts: 156, categories: { Travel: 26980, Food: 17040, Utility: 12780, Office: 8520, Other: 5680 }, avgPerReceipt: 455, topVendor: 'Amazon Business', budget: 60000, variance: 15.5 },
  { name: 'Jul', spend: 84230, receipts: 128, categories: { Travel: 32007, Food: 20215, Utility: 15161, Office: 10108, Other: 6739 }, avgPerReceipt: 658, topVendor: 'IndiGo Airlines', budget: 70000, variance: 16.9 },
];

// Enhanced monthly spending data for detailed analytics
const monthlySpendingDetails = {
  currentMonth: {
    name: 'July 2026',
    totalSpend: 84230,
    budget: 70000,
    budgetUsed: 120.3,
    variance: 16.9,
    receiptsCount: 128,
    avgPerReceipt: 658,
    avgPerDay: 2717,
    topCategories: [
      { name: 'Travel', amount: 32007, percentage: 38, change: 12.5, receipts: 45 },
      { name: 'Food', amount: 20215, percentage: 24, change: -8.2, receipts: 38 },
      { name: 'Utility', amount: 15161, percentage: 18, change: 15.1, receipts: 12 },
      { name: 'Office', amount: 10108, percentage: 12, change: 22.8, receipts: 25 },
      { name: 'Other', amount: 6739, percentage: 8, change: -5.5, receipts: 8 }
    ],
    topVendors: [
      { name: 'IndiGo Airlines', amount: 15240, receipts: 8, category: 'Travel' },
      { name: 'Amazon Business', amount: 8950, receipts: 15, category: 'Office' },
      { name: 'Cafe Coffee Day', amount: 4580, receipts: 12, category: 'Food' },
      { name: 'Uber', amount: 3240, receipts: 18, category: 'Travel' },
      { name: 'BESCOM Electricity', amount: 2890, receipts: 3, category: 'Utility' }
    ],
    weeklyBreakdown: [
      { week: 'Week 1', amount: 18450, receipts: 28, avgDaily: 2635 },
      { week: 'Week 2', amount: 24680, receipts: 35, avgDaily: 3526 },
      { week: 'Week 3', amount: 21890, receipts: 32, avgDaily: 3127 },
      { week: 'Week 4', amount: 19210, receipts: 33, avgDaily: 2744 }
    ],
    trends: {
      spendingTrend: 'increasing',
      trendPercentage: 18.7,
      peakDay: 'Friday',
      peakAmount: 12450,
      lowDay: 'Sunday',
      lowAmount: 1200
    }
  },
  previousMonth: {
    name: 'June 2026',
    totalSpend: 71000,
    receiptsCount: 156,
    avgPerReceipt: 455
  },
  yearToDate: {
    totalSpend: 400230,
    totalReceipts: 793,
    avgMonthly: 57176,
    projection: 686112
  }
};

const recentReceipts = [
  { 
    vendor: 'Cafe Turmeric', 
    amount: 640, 
    date: 'Jul 08', 
    category: 'Food', 
    status: 'validated', 
    tax: 51,
    receiptId: '#1200',
    items: [
      { name: 'Filter coffee x2', amount: 120 },
      { name: 'Masala dosa', amount: 180 },
      { name: 'Service & misc', amount: 289 }
    ]
  },
  { 
    vendor: 'IndiGo Airlines', 
    amount: 5240, 
    date: 'Jul 06', 
    category: 'Travel', 
    status: 'validated', 
    tax: 420,
    receiptId: '#1199',
    items: [
      { name: 'Fare — BLR→DEL', amount: 4300 },
      { name: 'Seat selection', amount: 240 },
      { name: 'Baggage', amount: 280 },
      { name: 'Convenience fee', amount: 420 }
    ]
  },
  { 
    vendor: 'BESCOM Electricity', 
    amount: 2380, 
    date: 'Jul 02', 
    category: 'Utility', 
    status: 'pending', 
    tax: 190,
    receiptId: '#1198',
    items: [
      { name: 'Electricity charges', amount: 1890 },
      { name: 'Fixed charges', amount: 300 },
      { name: 'Late fee', amount: 190 }
    ]
  },
  { 
    vendor: 'Amazon Business', 
    amount: 12500, 
    date: 'Jun 28', 
    category: 'Office', 
    status: 'validated', 
    tax: 2250,
    receiptId: '#1197',
    items: [
      { name: 'Office supplies', amount: 8500 },
      { name: 'Electronics', amount: 3200 },
      { name: 'Shipping charges', amount: 800 }
    ]
  },
  { 
    vendor: 'Ola Cabs', 
    amount: 450, 
    date: 'Jun 25', 
    category: 'Travel', 
    status: 'flagged', 
    tax: 36,
    receiptId: '#1196',
    items: [
      { name: 'Trip fare', amount: 380 },
      { name: 'Platform fee', amount: 34 },
      { name: 'Service tax', amount: 36 }
    ]
  },
  { 
    vendor: 'Swiggy', 
    amount: 890, 
    date: 'Jun 22', 
    category: 'Food', 
    status: 'validated', 
    tax: 71,
    receiptId: '#1195',
    items: [
      { name: 'Food items', amount: 750 },
      { name: 'Delivery charges', amount: 69 },
      { name: 'Packaging fee', amount: 71 }
    ]
  },
];

const validationAlerts = [
  { type: 'duplicate', message: 'Possible duplicate: Receipt #1289 matches #1043', severity: 'warning' },
  { type: 'tax', message: 'Tax rate mismatch in BESCOM bill (expected 8%, got 12%)', severity: 'error' },
  { type: 'compliance', message: 'GSTIN verified for Amazon Business', severity: 'success' },
];

const DashboardPage = () => {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [searchQuery, setSearchQuery] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showReceiptDetail, setShowReceiptDetail] = useState(false);
  const [selectedReceipt, setSelectedReceipt] = useState(null);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      type: 'validation',
      title: 'Receipt Validated',
      message: 'Cafe Turmeric receipt has been successfully validated',
      time: '2 minutes ago',
      unread: true,
      icon: CheckCircle2,
      color: '#10B981'
    },
    {
      id: 2,
      type: 'warning',
      title: 'Duplicate Receipt Detected',
      message: 'Possible duplicate found for BESCOM Electricity bill',
      time: '15 minutes ago',
      unread: true,
      icon: AlertTriangle,
      color: '#F59E0B'
    },
    {
      id: 3,
      type: 'upload',
      title: 'Upload Complete',
      message: 'Successfully processed 3 receipts from Amazon Business',
      time: '1 hour ago',
      unread: false,
      icon: Upload,
      color: '#6366F1'
    },
    {
      id: 4,
      type: 'error',
      title: 'Tax Rate Issue',
      message: 'Tax calculation mismatch detected in recent receipt',
      time: '3 hours ago',
      unread: true,
      icon: XCircle,
      color: '#EF4444'
    },
    {
      id: 5,
      type: 'info',
      title: 'Monthly Report Ready',
      message: 'Your July expense report is available for download',
      time: '5 hours ago',
      unread: false,
      icon: FileText,
      color: '#06B6D4'
    }
  ]);

  const handleReceiptClick = (receipt) => {
    setSelectedReceipt(receipt);
    setShowReceiptDetail(true);
  };

  const closeReceiptDetail = () => {
    setShowReceiptDetail(false);
    setSelectedReceipt(null);
  };

  const handleNotificationClick = () => {
    setShowNotifications(!showNotifications);
  };

  const markAsRead = (notificationId) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === notificationId 
          ? { ...notif, unread: false }
          : notif
      )
    );
  };

  const clearAllNotifications = () => {
    setNotifications(prev => 
      prev.map(notif => ({ ...notif, unread: false }))
    );
  };

  const getUnreadCount = () => {
    return notifications.filter(notif => notif.unread).length;
  };

  const toggleTheme = () => {
    const newTheme = !isDarkMode;
    setIsDarkMode(newTheme);
    const themeValue = newTheme ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', themeValue);
    localStorage.setItem('theme', themeValue);
  };

  // Close modals when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showNotifications && !event.target.closest('.notification-container')) {
        setShowNotifications(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showNotifications]);

  // Check if user is authenticated and initialize theme
  useEffect(() => {
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (!isLoggedIn) {
      navigate('/login');
    }

    // Initialize theme from localStorage or default to light mode
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      setIsDarkMode(true);
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      setIsDarkMode(false);
      document.documentElement.setAttribute('data-theme', 'light');
    }
  }, [navigate]);

  const handleLogout = () => {
    const confirmLogout = window.confirm('Are you sure you want to logout?');
    
    if (confirmLogout) {
      localStorage.removeItem('userEmail');
      localStorage.removeItem('userName');
      localStorage.removeItem('isLoggedIn');
      
      const logoutMessage = document.createElement('div');
      logoutMessage.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 1000;
        background: linear-gradient(135deg, #6366F1, #06B6D4);
        color: white; padding: 16px 24px; border-radius: 12px;
        font-weight: 600; box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
      `;
      logoutMessage.textContent = '👋 Logged out successfully!';
      document.body.appendChild(logoutMessage);
      
      setTimeout(() => {
        document.body.removeChild(logoutMessage);
        navigate('/');
      }, 1000);
    }
  };

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
    
    const files = Array.from(e.dataTransfer.files);
    handleFileUpload(files);
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    handleFileUpload(files);
  };

  const handleFileUpload = async (files) => {
    const validFiles = files.filter(file => {
      const validTypes = ['image/png', 'image/jpg', 'image/jpeg', 'application/pdf'];
      const maxSize = 10 * 1024 * 1024;
      
      if (!validTypes.includes(file.type)) {
        alert(`${file.name}: Invalid file type. Please upload PNG, JPG, or PDF files.`);
        return false;
      }
      
      if (file.size > maxSize) {
        alert(`${file.name}: File too large. Maximum size is 10MB.`);
        return false;
      }
      
      return true;
    });

    if (validFiles.length > 0) {
      try {
        setDragActive(false);
        alert('📤 Processing files... Please wait.');

        await new Promise(resolve => setTimeout(resolve, 2000));

        const mockResults = validFiles.map(file => {
          const mockMerchants = ['Cafe Coffee Day', 'Dominos Pizza', 'Uber Eats', 'Amazon', 'Flipkart', 'BigBasket'];
          const mockAmounts = [245, 480, 1250, 899, 650, 340];
          const randomIndex = Math.floor(Math.random() * mockMerchants.length);
          
          return {
            filename: file.name,
            status: 'success',
            merchant: mockMerchants[randomIndex],
            amount: mockAmounts[randomIndex] + Math.floor(Math.random() * 100),
            date: new Date().toLocaleDateString(),
            category: file.name.toLowerCase().includes('food') ? 'Food' : 
                     file.name.toLowerCase().includes('travel') ? 'Travel' : 'General'
          };
        });

        let messages = mockResults.map(result => 
          `✅ ${result.filename}:\n   ${result.merchant} - ₹${result.amount}\n   Category: ${result.category}`
        );

        const summary = `🎉 Upload Complete!\n\n` +
          `✅ Successfully processed ${validFiles.length} receipt(s)\n\n` +
          `Extracted Information:\n${messages.join('\n\n')}\n\n` +
          `💡 Demo Mode: In production, this would:\n` +
          `• Use AI-powered OCR to extract real data\n` +
          `• Validate against tax databases\n` +
          `• Store in secure database\n` +
          `• Update analytics dashboard`;

        alert(summary);
        setShowUploadModal(false);
        console.log('Files processed:', mockResults);

      } catch (error) {
        console.error('Upload error:', error);
        alert(`❌ Processing failed: ${error.message}`);
      }
    }
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
      icon: CheckCircle2,
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
          <button className="sidebar-item logout" onClick={handleLogout}>
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
            <button 
              className="header-btn theme-toggle" 
              onClick={toggleTheme}
              title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            <div className="user-profile" onClick={handleLogout} style={{ cursor: 'pointer' }}>
              <div className="user-avatar">
                {localStorage.getItem('userName') 
                  ? localStorage.getItem('userName').split(' ').map(n => n[0]).join('').toUpperCase()
                  : 'U'
                }
              </div>
              <div className="user-info hide-mobile">
                <div className="user-name">
                  {localStorage.getItem('userName') || 'User'}
                </div>
                <div className="user-role">Click to Logout</div>
              </div>
              <ChevronDown size={16} />
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <div className="dashboard-content">
          {activeTab === 'dashboard' && (
            <>
              <div className="dashboard-section-header">
                <h2>Dashboard Overview</h2>
                <p>Monitor your recent receipts and validation status</p>
              </div>

              <div className="dashboard-main-grid">
                {/* Recent Receipts */}
                <div className="panel-card large-panel receipts-section">
                  <div className="section-title">
                    Recent receipts 
                    <span className="count">— tap any slip</span>
                  </div>
                  <div className="receipt-grid">
                    {recentReceipts.map((receipt, i) => (
                      <div 
                        key={i} 
                        className={`slip slip-${i % 3}`}
                        onClick={() => handleReceiptClick(receipt)}
                      >
                        <div className="slip-top">
                          <div>
                            <div className="slip-vendor">{receipt.vendor}</div>
                            <div className="slip-meta">{receipt.date} · {receipt.category}</div>
                          </div>
                          <div className="slip-amount">₹{receipt.amount.toLocaleString('en-IN')}</div>
                        </div>
                        <div className="slip-foot">
                          <span className="slip-tax">Tax ₹{receipt.tax}</span>
                          <span className={`stamp-badge ${receipt.status}`}>
                            {receipt.status === 'validated' ? 'Validated' : 
                             receipt.status === 'pending' ? 'Pending' : 'Flagged'}
                          </span>
                        </div>
                        <div className="slip-after"></div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Validation Alerts */}
                <div className="panel-card validation-panel">
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

                  <div className="validation-stats">
                    <div className="stat-item">
                      <div className="stat-number">3</div>
                      <div className="stat-label">Pending Review</div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-number">15</div>
                      <div className="stat-label">Validated Today</div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-number">1</div>
                      <div className="stat-label">Needs Action</div>
                    </div>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="panel-card quick-actions-panel">
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
                    <button className="quick-action" onClick={() => setActiveTab('analytics')}>
                      <div className="qa-icon" style={{ background: 'rgba(34,211,238,0.2)', color: '#22D3EE' }}>
                        <BarChart3 size={20} />
                      </div>
                      <span>View Analytics</span>
                      <ArrowUpRight size={16} />
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'analytics' && (
            <>
              <div className="dashboard-section-header">
                <h2>Analytics & Insights</h2>
                <p>Comprehensive spending analysis and trends</p>
              </div>

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

              {/* Monthly Spending Chart Analytics */}
              <div className="monthly-analysis-section">
                <div className="section-title">
                  <h3>Monthly Spending Analysis - {monthlySpendingDetails.currentMonth.name}</h3>
                  <div className="month-selector">
                    <button className="month-nav">‹</button>
                    <span className="current-month">{monthlySpendingDetails.currentMonth.name}</span>
                    <button className="month-nav">›</button>
                  </div>
                </div>

                <div className="charts-analytics-grid">
                  {/* Budget Overview Radial Chart */}
                  <div className="chart-card budget-radial">
                    <div className="chart-header">
                      <h4>Budget Overview</h4>
                      <span className={`budget-status ${monthlySpendingDetails.currentMonth.budgetUsed > 100 ? 'over-budget' : 'within-budget'}`}>
                        {monthlySpendingDetails.currentMonth.budgetUsed.toFixed(1)}% Used
                      </span>
                    </div>
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Used', value: monthlySpendingDetails.currentMonth.totalSpend },
                            { name: 'Remaining', value: Math.max(0, monthlySpendingDetails.currentMonth.budget - monthlySpendingDetails.currentMonth.totalSpend) }
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={90}
                          paddingAngle={4}
                          dataKey="value"
                        >
                          <Cell fill={monthlySpendingDetails.currentMonth.budgetUsed > 100 ? "#EF4444" : "#10B981"} />
                          <Cell fill="rgba(255,255,255,0.1)" />
                        </Pie>
                        <Tooltip formatter={(value) => `₹${value.toLocaleString()}`} />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="budget-center-info">
                      <div className="budget-amount">₹{monthlySpendingDetails.currentMonth.totalSpend.toLocaleString()}</div>
                      <div className="budget-label">of ₹{monthlySpendingDetails.currentMonth.budget.toLocaleString()}</div>
                      <div className="budget-receipts">{monthlySpendingDetails.currentMonth.receiptsCount} receipts</div>
                    </div>
                  </div>

                  {/* Weekly Spending Bar Chart */}
                  <div className="chart-card weekly-bars">
                    <div className="chart-header">
                      <h4>Weekly Breakdown</h4>
                      <span className="week-info">4 weeks analysis</span>
                    </div>
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={monthlySpendingDetails.currentMonth.weeklyBreakdown}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="week" stroke="#64748B" fontSize={11} />
                        <YAxis stroke="#64748B" fontSize={11} />
                        <Tooltip formatter={(value) => `₹${value.toLocaleString()}`} />
                        <Bar dataKey="amount" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Category Distribution */}
                  <div className="chart-card category-donut">
                    <div className="chart-header">
                      <h4>Category Distribution</h4>
                      <span className="category-count">{monthlySpendingDetails.currentMonth.topCategories.length} categories</span>
                    </div>
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie
                          data={monthlySpendingDetails.currentMonth.topCategories}
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          dataKey="amount"
                          label={({name, percentage}) => `${name} ${percentage}%`}
                        >
                          {monthlySpendingDetails.currentMonth.topCategories.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={categoryData[index]?.color || '#8B5CF6'} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => `₹${value.toLocaleString()}`} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Top Vendors Horizontal Bar */}
                  <div className="chart-card vendors-horizontal">
                    <div className="chart-header">
                      <h4>Top Vendors</h4>
                      <span className="vendor-count">Top 5 vendors</span>
                    </div>
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={monthlySpendingDetails.currentMonth.topVendors} layout="horizontal">
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis type="number" stroke="#64748B" fontSize={11} />
                        <YAxis type="category" dataKey="name" stroke="#64748B" fontSize={10} width={80} />
                        <Tooltip formatter={(value) => `₹${value.toLocaleString()}`} />
                        <Bar dataKey="amount" fill="#F59E0B" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Monthly Expense Display Component */}
              <MonthlyExpenseDisplay />

              {/* Original Charts Row */}
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
            </>
          )}

          {activeTab === 'upload' && (
            <div className="dashboard-section-header">
              <h2>Upload Receipt</h2>
              <p>Upload and process your receipts</p>
              <button className="btn btn-primary" onClick={() => setShowUploadModal(true)}>
                <Upload size={18} />
                Upload New Receipt
              </button>
            </div>
          )}

          {activeTab === 'chat' && (
            <ChatPage />
          )}

          {activeTab === 'erp' && (
            <ERPPage />
          )}
        </div>
      </main>

      {/* Receipt Detail Modal */}
      {showReceiptDetail && selectedReceipt && (
        <div className="modal-overlay" onClick={closeReceiptDetail}>
          <div className="receipt-detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="receipt-detail-header">
              <h3>{selectedReceipt.vendor}</h3>
              <button className="modal-close" onClick={closeReceiptDetail}>✕</button>
            </div>
            
            <div className="receipt-detail-content">
              <div className="receipt-detail-meta">
                <span>{selectedReceipt.date} • {selectedReceipt.category} • Receipt {selectedReceipt.receiptId}</span>
              </div>
              
              <div className="receipt-items">
                {selectedReceipt.items.map((item, index) => (
                  <div key={index} className="receipt-item-line">
                    <span className="item-name">{item.name}</span>
                    <span className="item-amount">₹{item.amount.toLocaleString('en-IN')}</span>
                  </div>
                ))}
              </div>
              
              <div className="receipt-divider"></div>
              
              <div className="receipt-total-section">
                <div className="receipt-total-row">
                  <span className="total-label">TOTAL</span>
                  <span className="total-amount">₹{selectedReceipt.amount.toLocaleString('en-IN')}</span>
                </div>
              </div>
              
              {selectedReceipt.status === 'validated' && (
                <div className="validated-stamp">
                  <div className="stamp-circle">
                    <CheckCircle2 size={24} />
                    <div className="stamp-text">
                      <div className="stamp-main">VALIDATED</div>
                      <div className="stamp-sub">₹{selectedReceipt.tax}</div>
                    </div>
                  </div>
                </div>
              )}
              
              {selectedReceipt.status === 'pending' && (
                <div className="pending-stamp">
                  <div className="stamp-circle pending">
                    <AlertTriangle size={24} />
                    <div className="stamp-text">
                      <div className="stamp-main">PENDING</div>
                      <div className="stamp-sub">Review needed</div>
                    </div>
                  </div>
                </div>
              )}
              
              {selectedReceipt.status === 'flagged' && (
                <div className="flagged-stamp">
                  <div className="stamp-circle flagged">
                    <XCircle size={24} />
                    <div className="stamp-text">
                      <div className="stamp-main">FLAGGED</div>
                      <div className="stamp-sub">Needs attention</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

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
              <input
                type="file"
                id="file-upload"
                multiple
                accept=".png,.jpg,.jpeg,.pdf"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />
              <button 
                className="btn btn-primary upload-btn"
                onClick={() => document.getElementById('file-upload').click()}
              >
                Select Files
              </button>
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