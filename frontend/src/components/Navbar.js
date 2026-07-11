import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Receipt, Menu, X } from 'lucide-react';
import '../styles/Navbar.css';

const Navbar = () => {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const isLanding = location.pathname === '/';

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollTo = (id) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
    setMobileOpen(false);
  };

  return (
    <nav className={`navbar ${scrolled ? 'scrolled' : ''}`}>
      <div className="nav-brand">
        <div className="logo-mark">
          <Receipt size={22} color="#fff" strokeWidth={1.8} />
        </div>
        <Link to="/" className="logo-text">
          Receipt<span className="gradient-text">Vault</span>
        </Link>
      </div>

      {isLanding && (
        <div className={`nav-links ${mobileOpen ? 'open' : ''}`}>
          <button onClick={() => scrollTo('features')} className="nav-link">Features</button>
          <button onClick={() => scrollTo('how')} className="nav-link">How It Works</button>
          <Link to="/dashboard" className="nav-link">Dashboard</Link>
          <button onClick={() => scrollTo('cta')} className="nav-link">Get Started</button>
        </div>
      )}

      <div className="nav-cta">
        <Link to="/dashboard" className="btn btn-ghost">Sign In</Link>
        <Link to="/dashboard" className="btn btn-primary">Get Started</Link>
        <button className="mobile-toggle" onClick={() => setMobileOpen(!mobileOpen)}>
          {mobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
