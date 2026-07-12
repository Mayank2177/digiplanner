import React from 'react';
import { Link } from 'react-router-dom';
import { Play, ArrowRight } from 'lucide-react';
import ScrollReveal from './ScrollReveal';
import CountUp from './CountUp';
import '../styles/HeroSection.css';

const HeroSection = () => {
  return (
    <section className="hero">
      <div className="hero-grid">
        <div className="hero-content">
          <ScrollReveal>
            <div className="hero-badge">
              <span className="dot" />
              AI-POWERED EXPENSE INTELLIGENCE
            </div>
          </ScrollReveal>

          <ScrollReveal delay={1}>
            <h1 className="hero-title">
              Turn Receipts Into<br />
              <span className="gradient-text">Actionable Insights</span>
            </h1>
          </ScrollReveal>

          <ScrollReveal delay={2}>
            <p className="hero-sub">
              Upload, extract, and analyze every receipt with AI. Track spending, detect duplicates, 
              validate tax compliance, and sync with your ERP — all in one intelligent vault.
            </p>
          </ScrollReveal>

          <ScrollReveal delay={2}>
            <div className="hero-actions">
              <Link to="/signup" className="btn btn-primary hero-btn">
                Start Free Trial <ArrowRight size={18} />
              </Link>
              <button className="btn btn-ghost hero-btn">
                <Play size={16} fill="currentColor" /> Watch Demo
              </button>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={3}>
            <div className="hero-stats">
              <div className="hero-stat">
                <div className="stat-num">
                  <CountUp target={99.8} suffix="%" />
                </div>
                <div className="stat-label">Extraction Accuracy</div>
              </div>
              <div className="hero-stat">
                <div className="stat-num">
                  <CountUp target={2.4} suffix="M+" />
                </div>
                <div className="stat-label">Receipts Processed</div>
              </div>
              <div className="hero-stat">
                <div className="stat-num">
                  <CountUp target={0.3} suffix="s" />
                </div>
                <div className="stat-label">Avg. Processing</div>
              </div>
            </div>
          </ScrollReveal>
        </div>

        <ScrollReveal delay={2} className="hide-tablet">
          <div className="hero-visual">
            <div className="card-stack">
              <div className="stack-card">
                <div className="card-header">
                  <div className="card-icon">🧾</div>
                  <div>
                    <div className="card-title">IndiGo Airlines</div>
                    <div className="card-subtitle">Travel · Jul 06</div>
                  </div>
                </div>
                <div className="card-amount">₹5,240.00</div>
                <div className="card-meta">
                  <span>Tax: ₹420</span><span>•</span><span>Validated ✅</span>
                </div>
                <div className="card-bar"><div className="card-bar-fill" /></div>
              </div>
              <div className="stack-card card-2">
                <div className="card-header">
                  <div className="card-icon" style={{background:'linear-gradient(135deg,var(--neon-cyan),var(--neon-violet))'}}>☕</div>
                  <div>
                    <div className="card-title">Cafe Turmeric</div>
                    <div className="card-subtitle">Food · Jul 08</div>
                  </div>
                </div>
                <div className="card-amount" style={{color:'var(--neon-fuchsia)'}}>₹640.00</div>
                <div className="card-meta">
                  <span>Tax: ₹51</span><span>•</span><span>Validated ✅</span>
                </div>
                <div className="card-bar"><div className="card-bar-fill" style={{width:'45%'}} /></div>
              </div>
              <div className="stack-card card-3">
                <div className="card-header">
                  <div className="card-icon" style={{background:'linear-gradient(135deg,var(--neon-amber),var(--neon-rose))'}}>⚡</div>
                  <div>
                    <div className="card-title">BESCOM Electricity</div>
                    <div className="card-subtitle">Utility · Jul 02</div>
                  </div>
                </div>
                <div className="card-amount" style={{color:'var(--neon-amber)'}}>₹2,380.00</div>
                <div className="card-meta">
                  <span>Tax: ₹190</span><span>•</span><span>Validated ✅</span>
                </div>
                <div className="card-bar"><div className="card-bar-fill" style={{width:'62%'}} /></div>
              </div>
            </div>
            <div className="floating-elements">
              <div className="float-el">📊</div>
              <div className="float-el" style={{animationDelay:'1s'}}>🤖</div>
              <div className="float-el" style={{animationDelay:'2s'}}>💰</div>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
};

export default HeroSection;
