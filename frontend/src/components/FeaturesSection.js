import React from 'react';
import { ArrowRight } from 'lucide-react';
import ScrollReveal from './ScrollReveal';
import '../styles/FeaturesSection.css';

const features = [
  {
    icon: '🎯',
    title: 'Intelligent AI Parsing',
    desc: 'Google Gemini-powered extraction reads any receipt format with 99.8% accuracy. From handwritten bills to digital invoices — nothing escapes the vault. Automatic fallback to Tesseract + PaddleOCR ensures zero downtime.',
    large: true,
    stats: [
      { value: '99.8%', label: 'Accuracy', color: 'var(--neon-violet)' },
      { value: '0.3s', label: 'Latency', color: 'var(--neon-cyan)' }
    ]
  },
  {
    icon: '📊',
    title: 'Real-Time Analytics',
    desc: 'Interactive dashboards with spending trends, category breakdowns, vendor analysis, and predictive forecasting powered by polynomial regression.',
    gradient: 'linear-gradient(135deg,rgba(34,211,238,0.2),rgba(59,130,246,0.1))',
    border: 'rgba(34,211,238,0.2)'
  },
  {
    icon: '🤖',
    title: 'Automated Validation',
    desc: 'Smart checks for duplicate receipts, tax rate compliance, date integrity, and amount verification. Every receipt gets a validation score before hitting your ledger.',
    gradient: 'linear-gradient(135deg,rgba(251,191,36,0.2),rgba(245,158,11,0.1))',
    border: 'rgba(251,191,36,0.2)'
  },
  {
    icon: '🌍',
    title: 'Multi-Language Support',
    desc: 'Full i18n support with Hindi, English, and more. The interface and AI extraction adapt to your preferred language automatically.',
    gradient: 'linear-gradient(135deg,rgba(52,211,153,0.2),rgba(16,185,129,0.1))',
    border: 'rgba(52,211,153,0.2)'
  },
  {
    icon: '🔒',
    title: 'Bank-Grade Security',
    desc: 'Your financial data is encrypted at rest and in transit. Isolated vaults with strict access controls keep your receipts safe.',
    gradient: 'linear-gradient(135deg,rgba(251,113,133,0.2),rgba(244,63,94,0.1))',
    border: 'rgba(251,113,133,0.2)'
  },
  {
    icon: '🔌',
    title: 'ERP Integration',
    desc: 'Seamlessly sync with SAP, Oracle, ERPNext, Tally, and any REST endpoint. One-click export to CSV, Excel, PDF, and JSON formats.',
    gradient: 'linear-gradient(135deg,rgba(139,92,246,0.2),rgba(168,85,247,0.1))',
    border: 'rgba(139,92,246,0.2)'
  }
];

const FeaturesSection = () => {
  return (
    <section className="features-section" id="features">
      <div className="section-header">
        <ScrollReveal>
          <div className="section-tag">Core Capabilities</div>
        </ScrollReveal>
        <ScrollReveal delay={1}>
          <h2 className="section-title-main">
            Everything You Need to<br />
            <span className="gradient-text">Master Your Expenses</span>
          </h2>
        </ScrollReveal>
        <ScrollReveal delay={2}>
          <p className="section-subtitle">
            Powerful AI-driven tools that transform how you handle receipts, from upload to insight.
          </p>
        </ScrollReveal>
      </div>

      <div className="features-grid">
        {features.map((f, i) => (
          <ScrollReveal
            key={i}
            delay={f.large ? 0 : (i % 3) + 1}
            className={f.large ? 'feature-large' : ''}
          >
            <div className={`feature-card ${f.large ? 'large' : ''}`}>
              <div className="feature-glow" />
              {f.large ? (
                <div className="feature-content-large">
                  <div>
                    <div className="feature-icon">🎯</div>
                    <h3>{f.title}</h3>
                    <p>{f.desc}</p>
                    <span className="feature-link">Learn more <ArrowRight size={14} /></span>
                  </div>
                  <div className="feature-stats">
                    {f.stats.map((s, j) => (
                      <div key={j} className="feature-stat-box">
                        <div className="feature-stat-value" style={{ color: s.color }}>{s.value}</div>
                        <div className="feature-stat-label">{s.label}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <>
                  <div
                    className="feature-icon"
                    style={{
                      background: f.gradient,
                      borderColor: f.border
                    }}
                  >
                    {f.icon}
                  </div>
                  <h3>{f.title}</h3>
                  <p>{f.desc}</p>
                  <span className="feature-link">Learn more <ArrowRight size={14} /></span>
                </>
              )}
            </div>
          </ScrollReveal>
        ))}
      </div>
    </section>
  );
};

export default FeaturesSection;
