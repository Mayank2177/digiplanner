import React, { useState } from 'react';
import {
  Plug, Key, Globe, Database,
  CheckCircle2, AlertTriangle, XCircle, Clock,
  Copy, Eye, EyeOff, RefreshCw, Plus, Trash2,
  Edit3, ExternalLink, Activity, Zap,
  FileText, Download, Webhook,
  Play
} from 'lucide-react';
import '../styles/ERPPage.css';

const ERPPage = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [showApiKey, setShowApiKey] = useState({});
  const [connections, setConnections] = useState([
    {
      id: 1,
      name: 'SAP Business One',
      type: 'ERP',
      status: 'connected',
      lastSync: '2026-07-12T10:30:00Z',
      recordsSynced: 1250,
      logo: '🏢',
      endpoint: 'https://api.sap.com/b1',
      authType: 'OAuth 2.0',
      version: '10.0'
    },
    {
      id: 2,
      name: 'QuickBooks Online',
      type: 'Accounting',
      status: 'connected',
      lastSync: '2026-07-12T09:15:00Z',
      recordsSynced: 890,
      logo: '💚',
      endpoint: 'https://sandbox-quickbooks.api.intuit.com',
      authType: 'OAuth 2.0',
      version: '3.0'
    },
    {
      id: 3,
      name: 'NetSuite',
      type: 'ERP',
      status: 'error',
      lastSync: '2026-07-11T16:45:00Z',
      recordsSynced: 0,
      logo: '🌐',
      endpoint: 'https://rest.netsuite.com',
      authType: 'Token',
      version: '2023.2',
      error: 'Authentication failed - Token expired'
    },
    {
      id: 4,
      name: 'Microsoft Dynamics',
      type: 'ERP',
      status: 'pending',
      lastSync: null,
      recordsSynced: 0,
      logo: '🔷',
      endpoint: 'https://api.businesscentral.dynamics.com',
      authType: 'Azure AD',
      version: 'v2.0'
    }
  ]);

  const [apiKeys, setApiKeys] = useState([
    {
      id: 1,
      name: 'Production API Key',
      key: 'dp_prod_1234567890abcdef',
      created: '2026-06-15',
      lastUsed: '2026-07-12T08:30:00Z',
      permissions: ['read:receipts', 'write:receipts', 'read:analytics'],
      status: 'active',
      requests: 15420
    },
    {
      id: 2,
      name: 'Development API Key',
      key: 'dp_dev_abcdef1234567890',
      created: '2026-06-20',
      lastUsed: '2026-07-10T14:20:00Z',
      permissions: ['read:receipts', 'read:analytics'],
      status: 'active',
      requests: 2890
    },
    {
      id: 3,
      name: 'Staging API Key',
      key: 'dp_stg_567890abcdef1234',
      created: '2026-07-01',
      lastUsed: '2026-07-08T11:45:00Z',
      permissions: ['read:receipts'],
      status: 'inactive',
      requests: 450
    }
  ]);

  const [webhooks, setWebhooks] = useState([
    {
      id: 1,
      name: 'Receipt Processing Webhook',
      url: 'https://api.company.com/webhooks/receipt-processed',
      events: ['receipt.processed', 'receipt.validated'],
      status: 'active',
      deliveries: 1250,
      failures: 5,
      lastDelivery: '2026-07-12T10:15:00Z'
    },
    {
      id: 2,
      name: 'Analytics Update Webhook',
      url: 'https://dashboard.company.com/api/analytics',
      events: ['analytics.daily', 'analytics.monthly'],
      status: 'active',
      deliveries: 180,
      failures: 0,
      lastDelivery: '2026-07-12T06:00:00Z'
    }
  ]);

  const [syncLogs, setSyncLogs] = useState([
    { id: 1, timestamp: '2026-07-12T10:30:00Z', system: 'SAP Business One', action: 'sync_receipts', status: 'success', records: 45 },
    { id: 2, timestamp: '2026-07-12T10:25:00Z', system: 'QuickBooks Online', action: 'sync_expenses', status: 'success', records: 32 },
    { id: 3, timestamp: '2026-07-12T10:20:00Z', system: 'NetSuite', action: 'auth_refresh', status: 'error', error: 'Token expired' },
    { id: 4, timestamp: '2026-07-12T10:15:00Z', system: 'SAP Business One', action: 'sync_vendors', status: 'success', records: 8 },
    { id: 5, timestamp: '2026-07-12T10:10:00Z', system: 'QuickBooks Online', action: 'sync_receipts', status: 'success', records: 28 }
  ]);

  const formatTime = (timestamp) => {
    if (!timestamp) return 'Never';
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(timestamp));
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'connected':
      case 'active':
      case 'success':
        return <CheckCircle2 size={16} className="status-success" />;
      case 'pending':
        return <Clock size={16} className="status-pending" />;
      case 'error':
      case 'inactive':
        return <XCircle size={16} className="status-error" />;
      default:
        return <AlertTriangle size={16} className="status-warning" />;
    }
  };

  const toggleApiKeyVisibility = (id) => {
    setShowApiKey(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };

  const testConnection = (connectionId) => {
    // Simulate connection test
    console.log(`Testing connection for ${connectionId}`);
  };

  const syncConnection = (connectionId) => {
    // Simulate manual sync
    console.log(`Syncing connection ${connectionId}`);
  };

  return (
    <div className="erp-page">
      <div className="erp-header">
        <div className="header-content">
          <div className="header-icon">
            <Plug size={28} />
          </div>
          <div className="header-text">
            <h1>ERP & API Integration</h1>
            <p>Manage your system connections, API keys, and data synchronization</p>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary">
            <FileText size={18} />
            Documentation
          </button>
          <button className="btn btn-primary">
            <Plus size={18} />
            Add Integration
          </button>
        </div>
      </div>

      <div className="erp-tabs">
        <button 
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <Activity size={18} />
          Overview
        </button>
        <button 
          className={`tab ${activeTab === 'connections' ? 'active' : ''}`}
          onClick={() => setActiveTab('connections')}
        >
          <Database size={18} />
          Connections
        </button>
        <button 
          className={`tab ${activeTab === 'api-keys' ? 'active' : ''}`}
          onClick={() => setActiveTab('api-keys')}
        >
          <Key size={18} />
          API Keys
        </button>
        <button 
          className={`tab ${activeTab === 'webhooks' ? 'active' : ''}`}
          onClick={() => setActiveTab('webhooks')}
        >
          <Webhook size={18} />
          Webhooks
        </button>
        <button 
          className={`tab ${activeTab === 'logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          <FileText size={18} />
          Sync Logs
        </button>
      </div>

      <div className="erp-content">
        {activeTab === 'overview' && (
          <div className="overview-section">
            {/* Stats Cards */}
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-header">
                  <div className="stat-icon connected">
                    <CheckCircle2 size={20} />
                  </div>
                  <span className="stat-trend">+2 this month</span>
                </div>
                <div className="stat-value">4</div>
                <div className="stat-label">Active Connections</div>
              </div>
              
              <div className="stat-card">
                <div className="stat-header">
                  <div className="stat-icon synced">
                    <RefreshCw size={20} />
                  </div>
                  <span className="stat-trend">+15% vs last week</span>
                </div>
                <div className="stat-value">2,140</div>
                <div className="stat-label">Records Synced Today</div>
              </div>
              
              <div className="stat-card">
                <div className="stat-header">
                  <div className="stat-icon api">
                    <Zap size={20} />
                  </div>
                  <span className="stat-trend">98.5% uptime</span>
                </div>
                <div className="stat-value">18.7K</div>
                <div className="stat-label">API Requests (24h)</div>
              </div>
              
              <div className="stat-card">
                <div className="stat-header">
                  <div className="stat-icon webhooks">
                    <Globe size={20} />
                  </div>
                  <span className="stat-trend">99.2% success</span>
                </div>
                <div className="stat-value">1,430</div>
                <div className="stat-label">Webhook Deliveries</div>
              </div>
            </div>

            {/* System Status */}
            <div className="system-status-card">
              <div className="card-header">
                <h3>System Status</h3>
                <button className="refresh-btn">
                  <RefreshCw size={16} />
                  Refresh
                </button>
              </div>
              
              <div className="status-grid">
                {connections.map(connection => (
                  <div key={connection.id} className={`status-item ${connection.status}`}>
                    <div className="status-info">
                      <div className="system-icon">{connection.logo}</div>
                      <div className="system-details">
                        <div className="system-name">{connection.name}</div>
                        <div className="system-meta">{connection.type} • v{connection.version}</div>
                      </div>
                    </div>
                    <div className="status-indicator">
                      {getStatusIcon(connection.status)}
                      <span className="status-text">{connection.status}</span>
                    </div>
                    <div className="last-sync">
                      Last sync: {formatTime(connection.lastSync)}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Activity */}
            <div className="recent-activity-card">
              <div className="card-header">
                <h3>Recent Activity</h3>
                <button className="view-all-btn">
                  View All
                  <ExternalLink size={14} />
                </button>
              </div>
              
              <div className="activity-list">
                {syncLogs.slice(0, 5).map(log => (
                  <div key={log.id} className="activity-item">
                    <div className="activity-icon">
                      {getStatusIcon(log.status)}
                    </div>
                    <div className="activity-content">
                      <div className="activity-title">
                        {log.action.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} - {log.system}
                      </div>
                      <div className="activity-meta">
                        {log.status === 'success' && log.records && `${log.records} records processed • `}
                        {log.error && `Error: ${log.error} • `}
                        {formatTime(log.timestamp)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'connections' && (
          <div className="connections-section">
            <div className="section-header">
              <h3>System Connections</h3>
              <div className="header-actions">
                <button className="btn btn-secondary">
                  <Download size={16} />
                  Export Config
                </button>
                <button className="btn btn-primary">
                  <Plus size={16} />
                  Add Connection
                </button>
              </div>
            </div>

            <div className="connections-grid">
              {connections.map(connection => (
                <div key={connection.id} className={`connection-card ${connection.status}`}>
                  <div className="connection-header">
                    <div className="connection-icon">{connection.logo}</div>
                    <div className="connection-info">
                      <h4>{connection.name}</h4>
                      <span className="connection-type">{connection.type}</span>
                    </div>
                    <div className="connection-status">
                      {getStatusIcon(connection.status)}
                    </div>
                  </div>

                  <div className="connection-details">
                    <div className="detail-row">
                      <span className="detail-label">Endpoint:</span>
                      <span className="detail-value">{connection.endpoint}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Auth Type:</span>
                      <span className="detail-value">{connection.authType}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Version:</span>
                      <span className="detail-value">{connection.version}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Last Sync:</span>
                      <span className="detail-value">{formatTime(connection.lastSync)}</span>
                    </div>
                    {connection.recordsSynced > 0 && (
                      <div className="detail-row">
                        <span className="detail-label">Records Synced:</span>
                        <span className="detail-value">{connection.recordsSynced.toLocaleString()}</span>
                      </div>
                    )}
                    {connection.error && (
                      <div className="detail-row error">
                        <span className="detail-label">Error:</span>
                        <span className="detail-value">{connection.error}</span>
                      </div>
                    )}
                  </div>

                  <div className="connection-actions">
                    <button 
                      className="action-btn test"
                      onClick={() => testConnection(connection.id)}
                    >
                      <Activity size={14} />
                      Test
                    </button>
                    <button 
                      className="action-btn sync"
                      onClick={() => syncConnection(connection.id)}
                    >
                      <RefreshCw size={14} />
                      Sync
                    </button>
                    <button className="action-btn edit">
                      <Edit3 size={14} />
                      Edit
                    </button>
                    <button className="action-btn delete">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'api-keys' && (
          <div className="api-keys-section">
            <div className="section-header">
              <h3>API Keys</h3>
              <button className="btn btn-primary">
                <Plus size={16} />
                Generate New Key
              </button>
            </div>

            <div className="api-keys-list">
              {apiKeys.map(apiKey => (
                <div key={apiKey.id} className={`api-key-card ${apiKey.status}`}>
                  <div className="api-key-header">
                    <div className="key-info">
                      <h4>{apiKey.name}</h4>
                      <span className="key-id">Created {apiKey.created}</span>
                    </div>
                    <div className="key-status">
                      {getStatusIcon(apiKey.status)}
                      <span>{apiKey.status}</span>
                    </div>
                  </div>

                  <div className="api-key-details">
                    <div className="key-display">
                      <label>API Key:</label>
                      <div className="key-field">
                        <code className="key-value">
                          {showApiKey[apiKey.id] 
                            ? apiKey.key 
                            : apiKey.key.substring(0, 12) + '•'.repeat(20)
                          }
                        </code>
                        <button 
                          className="key-toggle"
                          onClick={() => toggleApiKeyVisibility(apiKey.id)}
                        >
                          {showApiKey[apiKey.id] ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                        <button 
                          className="key-copy"
                          onClick={() => copyToClipboard(apiKey.key)}
                        >
                          <Copy size={16} />
                        </button>
                      </div>
                    </div>

                    <div className="key-permissions">
                      <label>Permissions:</label>
                      <div className="permission-tags">
                        {apiKey.permissions.map((permission, index) => (
                          <span key={index} className="permission-tag">
                            {permission}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="key-stats">
                      <div className="stat">
                        <span className="stat-label">Last Used:</span>
                        <span className="stat-value">{formatTime(apiKey.lastUsed)}</span>
                      </div>
                      <div className="stat">
                        <span className="stat-label">Requests:</span>
                        <span className="stat-value">{apiKey.requests.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  <div className="api-key-actions">
                    <button className="action-btn edit">
                      <Edit3 size={14} />
                      Edit
                    </button>
                    <button className="action-btn regenerate">
                      <RefreshCw size={14} />
                      Regenerate
                    </button>
                    <button className="action-btn delete">
                      <Trash2 size={14} />
                      Revoke
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'webhooks' && (
          <div className="webhooks-section">
            <div className="section-header">
              <h3>Webhooks</h3>
              <button className="btn btn-primary">
                <Plus size={16} />
                Add Webhook
              </button>
            </div>

            <div className="webhooks-list">
              {webhooks.map(webhook => (
                <div key={webhook.id} className={`webhook-card ${webhook.status}`}>
                  <div className="webhook-header">
                    <div className="webhook-info">
                      <h4>{webhook.name}</h4>
                      <span className="webhook-url">{webhook.url}</span>
                    </div>
                    <div className="webhook-status">
                      {getStatusIcon(webhook.status)}
                      <span>{webhook.status}</span>
                    </div>
                  </div>

                  <div className="webhook-details">
                    <div className="webhook-events">
                      <label>Events:</label>
                      <div className="event-tags">
                        {webhook.events.map((event, index) => (
                          <span key={index} className="event-tag">
                            {event}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="webhook-stats">
                      <div className="stat">
                        <span className="stat-label">Deliveries:</span>
                        <span className="stat-value">{webhook.deliveries}</span>
                      </div>
                      <div className="stat">
                        <span className="stat-label">Failures:</span>
                        <span className="stat-value error">{webhook.failures}</span>
                      </div>
                      <div className="stat">
                        <span className="stat-label">Last Delivery:</span>
                        <span className="stat-value">{formatTime(webhook.lastDelivery)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="webhook-actions">
                    <button className="action-btn test">
                      <Play size={14} />
                      Test
                    </button>
                    <button className="action-btn edit">
                      <Edit3 size={14} />
                      Edit
                    </button>
                    <button className="action-btn delete">
                      <Trash2 size={14} />
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="logs-section">
            <div className="section-header">
              <h3>Synchronization Logs</h3>
              <div className="header-actions">
                <button className="btn btn-secondary">
                  <Download size={16} />
                  Export Logs
                </button>
                <button className="btn btn-secondary">
                  <RefreshCw size={16} />
                  Refresh
                </button>
              </div>
            </div>

            <div className="logs-table">
              <div className="table-header">
                <div className="th timestamp">Timestamp</div>
                <div className="th system">System</div>
                <div className="th action">Action</div>
                <div className="th status">Status</div>
                <div className="th records">Records</div>
                <div className="th details">Details</div>
              </div>
              
              <div className="table-body">
                {syncLogs.map(log => (
                  <div key={log.id} className={`table-row ${log.status}`}>
                    <div className="td timestamp">{formatTime(log.timestamp)}</div>
                    <div className="td system">{log.system}</div>
                    <div className="td action">{log.action.replace('_', ' ')}</div>
                    <div className="td status">
                      {getStatusIcon(log.status)}
                      <span>{log.status}</span>
                    </div>
                    <div className="td records">{log.records || '-'}</div>
                    <div className="td details">
                      {log.error || 'Completed successfully'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ERPPage;