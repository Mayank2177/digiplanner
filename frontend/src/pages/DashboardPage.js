import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Receipt, LayoutDashboard, Upload, BarChart3,
  Plug, LogOut, Search, Bell, Settings,
  ChevronDown, TrendingUp, MoreHorizontal,
  FileText, CheckCircle2,
  AlertTriangle, XCircle, ArrowUpRight,
  Sun, Moon
} from 'lucide-react';
import ERPPage from './ERPPage';
import MonthlyExpenseDisplay from '../components/MonthlyExpenseDisplay';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell
} from 'recharts';
import {
  isLoggedIn, clearSession, getMe, getReceipts, uploadReceipt,
  getBudgetSummary, getSpendByCategory, deleteReceipt as apiDeleteReceipt,
  getLineItems,
} from '../api/client';
import '../styles/DashboardPage.css';

// Colors reused for whichever categories come back from the backend
// (GET /api/v1/analytics/spend-by-category), since the API returns
// category names/totals but not colors.
const CATEGORY_COLORS = ['#8B5CF6', '#E879F9', '#22D3EE', '#FBBF24', '#34D399', '#F87171', '#60A5FA'];

function formatShortDate(isoDate) {
  if (!isoDate) return '';
  const d = new Date(isoDate);
  if (isNaN(d.getTime())) return isoDate;
  return d.toLocaleDateString('en-US', { month: 'short', day: '2-digit' });
}

function getCurrencySymbol(currencyCode) {
  const symbols = {
    'USD': '$',
    'INR': '₹',
    'EUR': '€',
    'GBP': '£',
    'JPY': '¥',
  };
  return symbols[currencyCode] || currencyCode;
}

function monthKey(isoDate) {
  return (isoDate || '').slice(0, 7); // "YYYY-MM"
}

function monthLabel(key) {
  const [y, m] = key.split('-');
  if (!y || !m) return key;
  const d = new Date(Number(y), Number(m) - 1, 1);
  return d.toLocaleDateString('en-US', { month: 'short' });
}

const sidebarItems = [
  { icon: Upload, label: 'Upload Receipt', id: 'upload' },
  { icon: LayoutDashboard, label: 'Dashboard', id: 'dashboard', active: true },
  { icon: BarChart3, label: 'Analytics', id: 'analytics' },
  { icon: Plug, label: 'ERP & API', id: 'erp' },
];

// NOTE: the static demo datasets that used to live here (spendingData,
// categoryData, monthlyData, monthlySpendingDetails, recentReceipts,
// validationAlerts) have been removed. All of that is now computed from
// real data fetched from the backend inside the DashboardPage component
// below (see the useMemo blocks for `categoryData`, `monthlyData`,
// `monthlySpendingDetails`, `recentReceiptsView`, and `validationAlerts`).


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

  // ── Real backend-backed state ──────────────────────────────────────────
  const [me, setMe] = useState(null);
  const [receipts, setReceipts] = useState([]);
  const [receiptsLoading, setReceiptsLoading] = useState(true);
  const [receiptsError, setReceiptsError] = useState(null);
  const [budgetSummary, setBudgetSummaryState] = useState(null);
  const [categoryBreakdown, setCategoryBreakdown] = useState([]);
  const [uploading, setUploading] = useState(false);

  const loadDashboardData = useCallback(async () => {
    console.log('[DEBUG] Starting loadDashboardData...');
    setReceiptsLoading(true);
    setReceiptsError(null);
    try {
      const [meData, receiptsData, budgetData, categorySpendData] = await Promise.all([
        getMe(),
        getReceipts(),
        getBudgetSummary(),
        getSpendByCategory(),
      ]);
      console.log('[DEBUG] Loaded data:', {
        receiptsCount: receiptsData.length,
        budget: budgetData,
        categories: categorySpendData.length
      });
      
      // Force state updates with new references to trigger re-renders
      setMe(meData);
      setReceipts(receiptsData);
      setBudgetSummaryState(budgetData);
      setCategoryBreakdown(categorySpendData);
      
      console.log('[DEBUG] State updated successfully');
    } catch (err) {
      console.error('[DEBUG] Error loading data:', err);
      setReceiptsError(err.message || 'Failed to load your data from the server.');
    } finally {
      setReceiptsLoading(false);
    }
  }, []); // Empty deps - function recreated only once

  const handleReceiptClick = async (receipt) => {
    setSelectedReceipt(receipt);
    setShowReceiptDetail(true);
    
    // Fetch line items for this receipt using centralized API
    try {
      const data = await getLineItems(receipt.billId);
      setSelectedReceipt({
        ...receipt,
        line_items: data.line_items || []
      });
    } catch (err) {
      console.error('Failed to fetch line items:', err);
      // Keep the receipt open even if line items fail
      setSelectedReceipt({
        ...receipt,
        line_items: []
      });
    }
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

  // Check if user is authenticated (has a real JWT), initialize theme, and
  // load real data from the backend (GET /api/v1/auth/me, /receipts,
  // /budget/summary, /analytics/spend-by-category).
  useEffect(() => {
    if (!isLoggedIn()) {
      navigate('/login');
      return;
    }

    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      setIsDarkMode(true);
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      setIsDarkMode(false);
      document.documentElement.setAttribute('data-theme', 'light');
    }

    loadDashboardData();
  }, [navigate, loadDashboardData]);

  const handleLogout = () => {
    const confirmLogout = window.confirm('Are you sure you want to logout?');
    
    if (confirmLogout) {
      clearSession();
      
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

  // Uploads files to the OCR pipeline. Uses batch endpoint for multiple files,
  // single upload endpoint for one file. Refreshes dashboard data on success.
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

    if (validFiles.length === 0) return;

    setDragActive(false);
    setUploading(true);

    try {
      if (validFiles.length === 1) {
        // Single file upload
        const saved = await uploadReceipt(validFiles[0]);
        alert(`🎉 Successfully processed receipt:\n\n✅ ${validFiles[0].name}:\n   ${saved.vendor} - $${saved.amount}\n   Category: ${saved.category}`);
      } else {
        // Batch upload - import the batch function
        const { uploadMultipleReceipts } = await import('../api/client');
        const result = await uploadMultipleReceipts(validFiles);
        
        let summary = `📊 Batch Upload Complete:\n\n`;
        summary += `✅ Successful: ${result.successful}\n`;
        summary += `⚠️ Failed: ${result.failed}\n`;
        summary += `🔄 Duplicates: ${result.duplicates}\n\n`;
        
        // Show details
        result.results.forEach(r => {
          if (r.status === 'success') {
            summary += `✅ ${r.filename}: ${r.receipt_data.vendor} - $${r.receipt_data.amount}\n`;
          } else if (r.status === 'duplicate') {
            summary += `🔄 ${r.filename}: ${r.message}\n`;
          } else {
            summary += `❌ ${r.filename}: ${r.message}\n`;
          }
        });
        
        alert(summary);
      }

      setShowUploadModal(false);
      
      // Force immediate refresh of all dashboard data
      console.log('[DEBUG] Upload successful, refreshing dashboard...');
      await loadDashboardData();
      console.log('[DEBUG] Dashboard refresh complete');
      
    } catch (err) {
      alert(`❌ Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteReceipt = async (billId) => {
    if (!window.confirm('Delete this receipt? This cannot be undone.')) return;
    try {
      await apiDeleteReceipt(billId);
      closeReceiptDetail();
      loadDashboardData();
    } catch (err) {
      alert(`❌ Could not delete receipt: ${err.message}`);
    }
  };

  // ── Everything below is derived from real backend data (receipts,
  // budgetSummary, categoryBreakdown loaded in loadDashboardData above)
  // instead of the static demo arrays this file used to have. ─────────────

  // Category Split / Category Distribution pie charts, from
  // GET /api/v1/analytics/spend-by-category.
  const categoryData = useMemo(() => {
    const total = categoryBreakdown.reduce((s, c) => s + (c.total || 0), 0);
    if (!total) return [];
    return categoryBreakdown.map((c, i) => ({
      name: c.category,
      value: Math.round((c.total / total) * 1000) / 10,
      color: CATEGORY_COLORS[i % CATEGORY_COLORS.length],
    }));
  }, [categoryBreakdown]);

  // "Spending Trend" area chart — every month present in the user's real
  // receipts, oldest to newest.
  const monthlyData = useMemo(() => {
    const buckets = new Map();
    receipts.forEach(r => {
      const key = monthKey(r.date);
      if (!key) return;
      if (!buckets.has(key)) buckets.set(key, { spend: 0, receipts: 0, vendors: {} });
      const b = buckets.get(key);
      b.spend += r.amount || 0;
      b.receipts += 1;
      b.vendors[r.vendor] = (b.vendors[r.vendor] || 0) + (r.amount || 0);
    });
    const budget = budgetSummary?.budget || 0;
    return Array.from(buckets.keys()).sort().map(key => {
      const b = buckets.get(key);
      const topVendor = Object.entries(b.vendors).sort((a, c) => c[1] - a[1])[0]?.[0] || '—';
      return {
        name: monthLabel(key),
        spend: b.spend,
        receipts: b.receipts,
        avgPerReceipt: b.receipts ? Math.round(b.spend / b.receipts) : 0,
        topVendor,
        budget,
        variance: budget ? Math.round(((b.spend - budget) / budget) * 1000) / 10 : 0,
      };
    });
  }, [receipts, budgetSummary]);

  // Analytics tab's "Monthly Spending Analysis" block — current calendar
  // month only, computed from real receipts + the real budget summary.
  const monthlySpendingDetails = useMemo(() => {
    const now = new Date();
    const currentKey = now.toISOString().slice(0, 7);
    const currentReceipts = receipts.filter(r => monthKey(r.date) === currentKey);
    const budget = budgetSummary?.budget || 0;
    const totalSpend = budgetSummary?.spent_this_month ?? currentReceipts.reduce((s, r) => s + (r.amount || 0), 0);
    const budgetUsed = budgetSummary?.percent_used ?? (budget ? (totalSpend / budget) * 100 : 0);
    const receiptsCount = currentReceipts.length;

    const catTotals = {};
    currentReceipts.forEach(r => {
      const cat = r.category || 'Uncategorized';
      catTotals[cat] = (catTotals[cat] || 0) + (r.amount || 0);
    });
    const topCategories = Object.entries(catTotals)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, amount]) => ({
        name,
        amount,
        percentage: totalSpend ? Math.round((amount / totalSpend) * 100) : 0,
        receipts: currentReceipts.filter(r => (r.category || 'Uncategorized') === name).length,
      }));

    const vendorTotals = {};
    currentReceipts.forEach(r => {
      if (!vendorTotals[r.vendor]) vendorTotals[r.vendor] = { amount: 0, receipts: 0, category: r.category };
      vendorTotals[r.vendor].amount += r.amount || 0;
      vendorTotals[r.vendor].receipts += 1;
    });
    const topVendors = Object.entries(vendorTotals)
      .sort((a, b) => b[1].amount - a[1].amount)
      .slice(0, 5)
      .map(([name, v]) => ({ name, amount: v.amount, receipts: v.receipts, category: v.category }));

    const weekBuckets = {};
    currentReceipts.forEach(r => {
      const d = new Date(r.date);
      const day = isNaN(d.getTime()) ? 1 : d.getDate();
      const label = `Week ${Math.min(4, Math.ceil(day / 7))}`;
      if (!weekBuckets[label]) weekBuckets[label] = { amount: 0, receipts: 0 };
      weekBuckets[label].amount += r.amount || 0;
      weekBuckets[label].receipts += 1;
    });
    const weeklyBreakdown = ['Week 1', 'Week 2', 'Week 3', 'Week 4'].map(label => ({
      week: label,
      amount: weekBuckets[label]?.amount || 0,
      receipts: weekBuckets[label]?.receipts || 0,
      avgDaily: Math.round((weekBuckets[label]?.amount || 0) / 7),
    }));

    return {
      currentMonth: {
        name: now.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
        totalSpend,
        budget,
        budgetUsed,
        receiptsCount,
        topCategories,
        topVendors,
        weeklyBreakdown,
      },
    };
  }, [receipts, budgetSummary]);

  // Recent receipts panel — the 6 most recently dated real receipts, or
  // (if the user typed something in the header search box) every real
  // receipt matching that vendor/category/amount text.
  const recentReceipts = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    const mapped = [...receipts]
      .sort((a, b) => (b.date || '').localeCompare(a.date || ''))
      .map(r => ({
        vendor: r.vendor,
        amount: r.amount,
        date: formatShortDate(r.date),
        category: r.category,
        status: 'validated',
        tax: r.tax,
        subtotal: r.subtotal,
        receiptId: r.bill_id,
        billId: r.bill_id,
        currency: r.currency || 'USD',
        currencySymbol: getCurrencySymbol(r.currency || 'USD'),
        line_items: [], // Will be populated when modal opens
      }));

    if (!q) return mapped; // Show all receipts

    return mapped.filter(r =>
      (r.vendor || '').toLowerCase().includes(q) ||
      (r.category || '').toLowerCase().includes(q) ||
      String(r.amount).includes(q)
    );
  }, [receipts, searchQuery]);

  // Validation Alerts panel — real, lightweight insights computed from the
  // receipts actually on file (exact vendor+amount+date repeats, receipts
  // the OCR pipeline couldn't categorize), not a scripted demo list.
  const validationAlerts = useMemo(() => {
    const alerts = [];
    const seen = new Set();
    receipts.forEach(r => {
      const key = `${r.vendor}|${r.amount}|${r.date}`;
      if (seen.has(key)) {
        alerts.push({ type: 'duplicate', message: `Possible duplicate: ${r.vendor} — $${r.amount} on ${r.date}`, severity: 'warning' });
      }
      seen.add(key);
    });
    const uncategorized = receipts.filter(r => !r.category || r.category === 'Uncategorized').length;
    if (uncategorized > 0) {
      alerts.push({ type: 'category', message: `${uncategorized} receipt(s) couldn't be auto-categorized — open one and edit its category`, severity: 'warning' });
    }
    if (receipts.length > 0) {
      alerts.push({ type: 'compliance', message: `${receipts.length} receipt(s) processed and saved to your vault`, severity: 'success' });
    }
    if (alerts.length === 0) {
      alerts.push({ type: 'info', message: 'No receipts yet — upload one to see validation insights here.', severity: 'success' });
    }
    return alerts;
  }, [receipts]);

  const totalSpendAll = receipts.reduce((s, r) => s + (r.amount || 0), 0);
  const totalTax = receipts.reduce((s, r) => s + (r.tax || 0), 0);
  const avgTaxRate = totalSpendAll ? ((totalTax / totalSpendAll) * 100).toFixed(1) : '0';

  const kpiCards = [
    {
      label: 'Total Spend',
      value: `$${totalSpendAll.toLocaleString('en-IN')}`,
      delta: `${receipts.length} receipt(s) total`,
      deltaPositive: true,
      icon: TrendingUp,
      color: 'var(--neon-violet)'
    },
    {
      label: 'Receipts',
      value: `${receipts.length}`,
      delta: `${monthlySpendingDetails.currentMonth.receiptsCount} this month`,
      deltaPositive: true,
      icon: FileText,
      color: 'var(--neon-cyan)'
    },
    {
      label: 'Tax Paid',
      value: `$${totalTax.toLocaleString('en-IN')}`,
      delta: `${avgTaxRate}% avg rate`,
      deltaPositive: true,
      icon: CheckCircle2,
      color: 'var(--neon-emerald)'
    },
    {
      label: 'Avg / Receipt',
      value: `$${receipts.length ? Math.round(totalSpendAll / receipts.length).toLocaleString('en-IN') : 0}`,
      delta: 'across all receipts',
      deltaPositive: true,
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
              <div className="goal-label">MONTHLY BUDGET</div>
              <div className="goal-value">
                ₹{Math.round(budgetSummary?.spent_this_month || 0).toLocaleString('en-IN')} / ₹{Math.round(budgetSummary?.budget || 0).toLocaleString('en-IN')}
              </div>
              <div className="goal-bar">
                <div className="goal-fill" style={{ width: `${Math.min(100, budgetSummary?.percent_used || 0)}%` }} />
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
            <div className="notification-container" style={{ position: 'relative' }}>
              <button className="header-btn" onClick={handleNotificationClick}>
                <Bell size={20} />
                {getUnreadCount() > 0 && <span className="badge">{getUnreadCount()}</span>}
              </button>
              {showNotifications && (
                <div
                  style={{
                    position: 'absolute', top: '48px', right: 0, width: '320px',
                    maxHeight: '360px', overflowY: 'auto', background: '#1A1A3E',
                    border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px',
                    boxShadow: '0 12px 32px rgba(0,0,0,0.4)', zIndex: 50, padding: '8px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 8px 4px' }}>
                    <strong style={{ fontSize: '14px' }}>Notifications</strong>
                    <button
                      onClick={clearAllNotifications}
                      style={{ background: 'none', border: 'none', color: '#8B5CF6', cursor: 'pointer', fontSize: '12px' }}
                    >
                      Mark all read
                    </button>
                  </div>
                  {notifications.map((n) => (
                    <div
                      key={n.id}
                      onClick={() => markAsRead(n.id)}
                      style={{
                        display: 'flex', gap: '10px', padding: '10px 8px',
                        opacity: n.unread ? 1 : 0.55, cursor: 'pointer',
                        borderBottom: '1px solid rgba(255,255,255,0.06)',
                      }}
                    >
                      <n.icon size={18} color={n.color} style={{ flexShrink: 0, marginTop: '2px' }} />
                      <div>
                        <div style={{ fontSize: '13px', fontWeight: 600 }}>{n.title}</div>
                        <div style={{ fontSize: '12px', opacity: 0.75 }}>{n.message}</div>
                        <div style={{ fontSize: '11px', opacity: 0.5, marginTop: '2px' }}>{n.time}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
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
                {(me?.name || localStorage.getItem('userName'))
                  ? (me?.name || localStorage.getItem('userName')).split(' ').map(n => n[0]).join('').toUpperCase()
                  : 'U'
                }
              </div>
              <div className="user-info hide-mobile">
                <div className="user-name">
                  {me?.name || localStorage.getItem('userName') || 'User'}
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
                {/* Debug info - remove after testing */}
                <div style={{fontSize: '11px', opacity: 0.6, marginTop: '8px'}}>
                  Debug: {receipts.length} receipts | Budget: ₹{budgetSummary?.budget || 0} | 
                  Spent: ₹{budgetSummary?.spent_this_month || 0} | 
                  Last updated: {new Date().toLocaleTimeString()}
                </div>
              </div>

              <div className="dashboard-main-grid">
                {/* Recent Receipts */}
                <div className="panel-card large-panel receipts-section">
                  <div className="section-title">
                    Recent receipts 
                    <span className="count">— tap any slip</span>
                  </div>
                  <div className="receipt-grid">
                    {receiptsLoading && <div style={{ opacity: 0.6, padding: '12px' }}>Loading your receipts…</div>}
                    {!receiptsLoading && receiptsError && (
                      <div style={{ color: '#EF4444', padding: '12px' }}>{receiptsError}</div>
                    )}
                    {!receiptsLoading && !receiptsError && recentReceipts.length === 0 && (
                      <div style={{ opacity: 0.6, padding: '12px' }}>
                        No receipts yet — click "Upload Receipt" to add your first one.
                      </div>
                    )}
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
                            {receipt.status === 'validated' ? 'Saved' : 
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
                      <div className="stat-number">
                        {receipts.filter(r => !r.category || r.category === 'Uncategorized').length}
                      </div>
                      <div className="stat-label">Needs Category</div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-number">
                        {receipts.filter(r => r.date === new Date().toISOString().slice(0, 10)).length}
                      </div>
                      <div className="stat-label">Saved Today</div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-number">
                        {validationAlerts.filter(a => a.type === 'duplicate').length}
                      </div>
                      <div className="stat-label">Possible Duplicates</div>
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
              <MonthlyExpenseDisplay receipts={receipts} budget={budgetSummary?.budget || 0} />

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
              
              {/* Show line items if available */}
              {selectedReceipt.line_items && selectedReceipt.line_items.length > 0 && (
                <>
                  <div className="receipt-items">
                    <div className="receipt-items-header">
                      <span>Line Items</span>
                    </div>
                    {selectedReceipt.line_items.map((item, index) => (
                      <div key={index} className="receipt-item-line">
                        <div className="item-info">
                          <span className="item-name">{item.name}</span>
                          {item.quantity > 1 && (
                            <span className="item-quantity"> x{item.quantity}</span>
                          )}
                        </div>
                        <span className="item-amount">
                          {selectedReceipt.currencySymbol}{item.total_price?.toFixed(2) || '0.00'}
                        </span>
                      </div>
                    ))}
                  </div>
                  <div className="receipt-divider"></div>
                </>
              )}
              
              {/* Show subtotal and tax breakdown */}
              <div className="receipt-items">
                <div className="receipt-item-line">
                  <span className="item-name">Subtotal</span>
                  <span className="item-amount">
                    {selectedReceipt.currencySymbol}{(selectedReceipt.subtotal || 0).toFixed(2)}
                  </span>
                </div>
                <div className="receipt-item-line">
                  <span className="item-name">Tax</span>
                  <span className="item-amount">
                    {selectedReceipt.currencySymbol}{(selectedReceipt.tax || 0).toFixed(2)}
                  </span>
                </div>
              </div>
              
              <div className="receipt-divider"></div>
              
              <div className="receipt-total-section">
                <div className="receipt-total-row">
                  <span className="total-label">TOTAL</span>
                  <span className="total-amount">
                    {selectedReceipt.currencySymbol}{selectedReceipt.amount.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                  </span>
                </div>
              </div>
              
              {selectedReceipt.status === 'validated' && (
                <div className="validated-stamp">
                  <div className="stamp-circle">
                    <CheckCircle2 size={24} />
                    <div className="stamp-text">
                      <div className="stamp-main">SAVED</div>
                      <div className="stamp-sub">Tax: ₹{selectedReceipt.tax}</div>
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

              <button
                className="btn-secondary"
                style={{ marginTop: '16px', width: '100%', color: '#EF4444', borderColor: '#EF4444' }}
                onClick={() => handleDeleteReceipt(selectedReceipt.billId)}
              >
                Delete Receipt
              </button>
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
              <p className="upload-title">{uploading ? 'Processing your receipt(s)…' : 'Drag & drop your receipts here'}</p>
              <p className="upload-sub">or click to browse (PNG, JPG, PDF)</p>
              <input
                type="file"
                id="file-upload"
                multiple
                accept=".png,.jpg,.jpeg,.pdf"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
                disabled={uploading}
              />
              <button 
                className="btn btn-primary upload-btn"
                onClick={() => document.getElementById('file-upload').click()}
                disabled={uploading}
              >
                {uploading ? 'Uploading…' : 'Select Files'}
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