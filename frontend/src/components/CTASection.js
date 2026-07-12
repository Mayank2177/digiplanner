import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import ScrollReveal from './ScrollReveal';
import '../styles/CTASection.css';

const CTASection = () => {
  return (
    <section className="cta-section" id="cta">
      <ScrollReveal>
        <div className="cta-container">
          <h2 className="cta-title">
            Ready to Transform Your<br />
            <span className="gradient-text">Expense Workflow?</span>
          </h2>
          <p className="cta-sub">
            Join 10,000+ businesses already using ReceiptVault. Start your free 14-day trial today.
          </p>
          <Link to="/signup" className="btn btn-primary cta-btn">
            Get Started for Free <ArrowRight size={20} />
          </Link>
        </div>
      </ScrollReveal>
    </section>
  );
};

export default CTASection;
