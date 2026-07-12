import React, { useState } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import { BarChart3, Table, Calendar, TrendingUp } from 'lucide-react';
import '../styles/MonthlyExpenseDisplay.css';

const MonthlyExpenseDisplay = () => {
  const [viewMode, setViewMode] = useState('chart'); // 'table' or 'chart'
  const [chartType, setChartType] = useState('bar'); // 'bar', 'line', 'area', 'pie'

  // Monthly expense data
  const monthlyData = [
    { 
      month: 'Jan 2026', 
      totalSpend: 42000, 
      travel: 15800, 
      food: 10080, 
      utility: 7560, 
      office: 5040, 
      other: 3360,
      receipts: 89,
      budget: 45000,
      variance: -7.1
    },
    { 
      month: 'Feb 2026', 
      totalSpend: 38000, 
      travel: 14440, 
      food: 9120, 
      utility: 6840, 
      office: 4560, 
      other: 3040,
      receipts: 76,
      budget: 45000,
      variance: -18.4
    },
    { 
      month: 'Mar 2026', 
      totalSpend: 55000, 
      travel: 20900, 
      food: 13200, 
      utility: 9900, 
      office: 6600, 
      other: 4400,
      receipts: 112,
      budget: 45000,
      variance: 18.2
    },
    { 
      month: 'Apr 2026', 
      totalSpend: 48000, 
      travel: 18240, 
      food: 11520, 
      utility: 8640, 
      office: 5760, 
      other: 3840,
      receipts: 98,
      budget: 50000,
      variance: -4.0
    },
    { 
      month: 'May 2026', 
      totalSpend: 62000, 
      travel: 23560, 
      food: 14880, 
      utility: 11160, 
      office: 7440, 
      other: 4960,
      receipts: 134,
      budget: 55000,
      variance: 11.3
    },
    { 
      month: 'Jun 2026', 
      totalSpend: 71000, 
      travel: 26980, 
      food: 17040, 
      utility: 12780, 
      office: 8520, 
      other: 5680,
      receipts: 156,
      budget: 60000,
      variance: 15.5
    },
    { 
      month: 'Jul 2026', 
      totalSpend: 84230, 
      travel: 32007, 
      food: 20215, 
      utility: 15161, 
      office: 10108, 
      other: 6739,
      receipts: 128,
      budget: 70000,
      variance: 16.9
    }
  ];

  // Category colors
  const categoryColors = {
    travel: '#8B5CF6',
    food: '#E879F9',
    utility: '#22D3EE',
    office: '#FBBF24',
    other: '#34D399'
  };

  // Prepare data for pie chart (latest month breakdown)
  const pieData = [
    { name: 'Travel', value: monthlyData[monthlyData.length - 1].travel, color: categoryColors.travel },
    { name: 'Food', value: monthlyData[monthlyData.length - 1].food, color: categoryColors.food },
    { name: 'Utility', value: monthlyData[monthlyData.length - 1].utility, color: categoryColors.utility },
    { name: 'Office', value: monthlyData[monthlyData.length - 1].office, color: categoryColors.office },
    { name: 'Other', value: monthlyData[monthlyData.length - 1].other, color: categoryColors.other }
  ];

  const formatCurrency = (value) => `₹${value.toLocaleString('en-IN')}`;
  
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
              <th>Travel</th>
              <th>Food</th>
              <th>Utility</th>
              <th>Office</th>
              <th>Other</th>
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
                <td>{formatCurrency(row.travel)}</td>
                <td>{formatCurrency(row.food)}</td>
                <td>{formatCurrency(row.utility)}</td>
                <td>{formatCurrency(row.office)}</td>
                <td>{formatCurrency(row.other)}</td>
                <td className="receipts-count">{row.receipts}</td>
                <td>{formatCurrency(row.budget)}</td>
                <td className={`variance ${getVarianceClass(row.variance)}`}>
                  {formatPercent(row.variance)}
                </td>
              </tr>
            ))}
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
              <div className="stat-value">₹{(monthlyData.reduce((sum, month) => sum + month.totalSpend, 0) / monthlyData.length / 1000).toFixed(0)}K</div>
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