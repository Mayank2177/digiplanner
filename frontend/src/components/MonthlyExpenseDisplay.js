import React, { useState, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import { BarChart3, Table, Calendar, TrendingUp } from 'lucide-react';
import '../styles/MonthlyExpenseDisplay.css';

const PALETTE = ['#8B5CF6', '#E879F9', '#22D3EE', '#FBBF24', '#34D399', '#F87171', '#60A5FA'];

// Builds the same shape the old hardcoded mock used (month, totalSpend,
// per-category totals, receipts, budget, variance) but from the user's
// real receipts (passed in as a prop from DashboardPage, which already
// fetched them from GET /api/v1/receipts) and their real budget
// (GET /api/v1/budget/summary). Categories are whatever the OCR pipeline
// / user actually assigned — not a fixed Travel/Food/Utility/Office/Other
// list — so the top categories present in the data are used as columns.
function buildMonthlyBreakdown(receipts, budget) {
  const byMonth = new Map();
  for (const r of receipts) {
    const key = (r.date || '').slice(0, 7); // "YYYY-MM"
    if (!key) continue;
    if (!byMonth.has(key)) byMonth.set(key, { totalSpend: 0, receipts: 0, categories: {} });
    const bucket = byMonth.get(key);
    bucket.totalSpend += r.amount || 0;
    bucket.receipts += 1;
    bucket.categories[r.category || 'Uncategorized'] =
      (bucket.categories[r.category || 'Uncategorized'] || 0) + (r.amount || 0);
  }

  const categoryTotals = {};
  receipts.forEach(r => {
    const cat = r.category || 'Uncategorized';
    categoryTotals[cat] = (categoryTotals[cat] || 0) + (r.amount || 0);
  });
  const topCategories = Object.entries(categoryTotals)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([name], i) => ({ name, color: PALETTE[i % PALETTE.length] }));

  const sortedKeys = Array.from(byMonth.keys()).sort();
  const monthlyData = sortedKeys.map(key => {
    const bucket = byMonth.get(key);
    const [y, m] = key.split('-');
    const label = new Date(Number(y), Number(m) - 1, 1).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    const variance = budget ? ((bucket.totalSpend - budget) / budget) * 100 : 0;
    const row = {
      month: label,
      totalSpend: bucket.totalSpend,
      receipts: bucket.receipts,
      budget: budget || 0,
      variance,
    };
    topCategories.forEach(({ name }) => {
      row[name] = bucket.categories[name] || 0;
    });
    return row;
  });

  return { monthlyData, topCategories };
}

const MonthlyExpenseDisplay = ({ receipts = [], budget = 0 }) => {
  const [viewMode, setViewMode] = useState('chart'); // 'table' or 'chart'
  const [chartType, setChartType] = useState('bar'); // 'bar', 'line', 'area', 'pie'

  const { monthlyData, topCategories } = useMemo(
    () => buildMonthlyBreakdown(receipts, budget),
    [receipts, budget]
  );

  const hasData = monthlyData.length > 0;
  const latestMonth = hasData ? monthlyData[monthlyData.length - 1] : null;

  // Prepare data for pie chart (latest month breakdown)
  const pieData = latestMonth
    ? topCategories.map(({ name, color }) => ({ name, value: latestMonth[name] || 0, color }))
    : [];

  const formatCurrency = (value) => `₹${(value || 0).toLocaleString('en-IN')}`;
  
  const formatPercent = (value) => `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;

  const getVarianceClass = (variance) => variance > 0 ? 'positive' : 'negative';

  const renderChart = () => {
    switch (chartType) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={monthlyData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="month" 
                stroke="#64748B" 
                fontSize={12}
                tick={{ fill: '#64748B' }}
              />
              <YAxis 
                stroke="#64748B" 
                fontSize={12}
                tick={{ fill: '#64748B' }}
                tickFormatter={(value) => `₹${(value/1000).toFixed(0)}K`}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1E293B',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  color: '#F8FAFC'
                }}
                formatter={(value) => [formatCurrency(value), 'Total Spend']}
              />
              <Bar dataKey="totalSpend" fill="url(#barGradient)" radius={[4, 4, 0, 0]} />
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.8} />
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={monthlyData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="month" 
                stroke="#64748B" 
                fontSize={12}
                tick={{ fill: '#64748B' }}
              />
              <YAxis 
                stroke="#64748B" 
                fontSize={12}
                tick={{ fill: '#64748B' }}
                tickFormatter={(value) => `₹${(value/1000).toFixed(0)}K`}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1E293B',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  color: '#F8FAFC'
                }}
                formatter={(value) => [formatCurrency(value), 'Total Spend']}
              />
              <Line 
                type="monotone" 
                dataKey="totalSpend" 
                stroke="#8B5CF6" 
                strokeWidth={3}
                dot={{ fill: '#8B5CF6', strokeWidth: 2, r: 6 }}
                activeDot={{ r: 8, stroke: '#8B5CF6', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={monthlyData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <defs>
                <linearGradient id="colorSpend" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="month" 
                stroke="#64748B" 
                fontSize={12}
                tick={{ fill: '#64748B' }}
              />
              <YAxis 
                stroke="#64748B" 
                fontSize={12}
                tick={{ fill: '#64748B' }}
                tickFormatter={(value) => `₹${(value/1000).toFixed(0)}K`}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1E293B',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  color: '#F8FAFC'
                }}
                formatter={(value) => [formatCurrency(value), 'Total Spend']}
              />
              <Area 
                type="monotone" 
                dataKey="totalSpend" 
                stroke="#8B5CF6" 
                strokeWidth={2}
                fill="url(#colorSpend)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={120}
                paddingAngle={4}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1E293B',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  color: '#F8FAFC'
                }}
                formatter={(value) => [formatCurrency(value), 'Amount']}
              />
            </PieChart>
          </ResponsiveContainer>
        );

      default:
        return null;
    }
  };

  const renderTable = () => (
    <div className="expense-table-container">
      <div className="table-wrapper">
        <table className="expense-table">
          <thead>
            <tr>
              <th>Month</th>
              <th>Total Spend</th>
              {topCategories.map(({ name }) => <th key={name}>{name}</th>)}
              <th>Receipts</th>
              <th>Budget</th>
              <th>Variance</th>
            </tr>
          </thead>
          <tbody>
            {monthlyData.map((row, index) => (
              <tr key={index} className="table-row">
                <td className="month-cell">
                  <Calendar size={16} />
                  {row.month}
                </td>
                <td className="total-spend">
                  {formatCurrency(row.totalSpend)}
                </td>
                {topCategories.map(({ name }) => (
                  <td key={name}>{formatCurrency(row[name])}</td>
                ))}
                <td className="receipts-count">{row.receipts}</td>
                <td>{formatCurrency(row.budget)}</td>
                <td className={`variance ${getVarianceClass(row.variance)}`}>
                  {formatPercent(row.variance)}
                </td>
              </tr>
            ))}
            {!hasData && (
              <tr>
                <td colSpan={4 + topCategories.length} style={{ textAlign: 'center', opacity: 0.6, padding: '24px' }}>
                  No receipts yet — upload one to see your monthly breakdown here.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div className="monthly-expense-display">
      <div className="expense-header">
        <div className="header-left">
          <h3>Monthly Expense Analysis</h3>
          <p>Track your spending patterns across months and categories</p>
        </div>
        <div className="header-controls">
          <div className="view-toggle">
            <button 
              className={`toggle-btn ${viewMode === 'table' ? 'active' : ''}`}
              onClick={() => setViewMode('table')}
            >
              <Table size={18} />
              Table
            </button>
            <button 
              className={`toggle-btn ${viewMode === 'chart' ? 'active' : ''}`}
              onClick={() => setViewMode('chart')}
            >
              <BarChart3 size={18} />
              Chart
            </button>
          </div>
          
          {viewMode === 'chart' && (
            <div className="chart-type-selector">
              <select 
                value={chartType} 
                onChange={(e) => setChartType(e.target.value)}
                className="chart-select"
              >
                <option value="bar">Bar Chart</option>
                <option value="line">Line Chart</option>
                <option value="area">Area Chart</option>
                <option value="pie">Pie Chart (Current Month)</option>
              </select>
            </div>
          )}
        </div>
      </div>

      <div className="expense-content">
        {viewMode === 'table' ? renderTable() : renderChart()}
      </div>

      {viewMode === 'chart' && chartType === 'pie' && (
        <div className="pie-legend">
          <div className="legend-items">
            {pieData.map((item, index) => (
              <div key={index} className="legend-item">
                <span 
                  className="legend-dot" 
                  style={{ backgroundColor: item.color }}
                />
                <span className="legend-label">{item.name}</span>
                <span className="legend-value">{formatCurrency(item.value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="expense-summary">
        <div className="summary-stats">
          <div className="stat-item">
            <TrendingUp size={20} />
            <div className="stat-content">
              <div className="stat-value">₹{hasData ? (monthlyData.reduce((sum, month) => sum + month.totalSpend, 0) / monthlyData.length / 1000).toFixed(0) : '0'}K</div>
              <div className="stat-label">Avg Monthly</div>
            </div>
          </div>
          <div className="stat-item">
            <Calendar size={20} />
            <div className="stat-content">
              <div className="stat-value">{monthlyData.length}</div>
              <div className="stat-label">Months Tracked</div>
            </div>
          </div>
          <div className="stat-item">
            <BarChart3 size={20} />
            <div className="stat-content">
              <div className="stat-value">{monthlyData.reduce((sum, month) => sum + month.receipts, 0)}</div>
              <div className="stat-label">Total Receipts</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MonthlyExpenseDisplay;