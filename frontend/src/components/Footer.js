import React from 'react';
import { Link } from 'react-router-dom';
import { Receipt } from 'lucide-react';
import '../styles/Footer.css';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-grid">
        <div className="footer-brand">
          <div className="logo-text">
            Receipt<span className="gradient-text">Vault</span>
          </div>
          <p>AI-powered receipt extraction, validation, and analytics for modern finance teams. Built for India, loved worldwide.</p>
          <div className="footer-social">
            <a href="#">𝕏</a>
            <a href="#">in</a>
            <a href="#">📧</a>
            <a href="#">🐙</a>
          </div>
        </div>
        <div className="footer-col">
          <h4>Product</h4>
          <Link to="/">Features</Link>
          <Link to="/">Pricing</Link>
          <Link to="/">Integrations</Link>
          <Link to="/">API Docs</Link>
          <Link to="/">Changelog</Link>
        </div>
        <div className="footer-col">
          <h4>Company</h4>
          <Link to="/">About</Link>
          <Link to="/">Blog</Link>
          <Link to="/">Careers</Link>
          <Link to="/">Contact</Link>
          <Link to="/">Partners</Link>
        </div>
        <div className="footer-col">
          <h4>Legal</h4>
          <Link to="/">Privacy Policy</Link>
          <Link to="/">Terms of Service</Link>
          <Link to="/">Cookie Policy</Link>
          <Link to="/">Security</Link>
          <Link to="/">Compliance</Link>
        </div>
      </div>
      <div className="footer-bottom">
        <div>© 2026 ReceiptVault. All rights reserved.</div>
        <div className="footer-legal-links">
          <Link to="/">Privacy</Link>
          <Link to="/">Terms</Link>
          <Link to="/">Cookies</Link>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
