import React from 'react';
import ScrollReveal from './ScrollReveal';
import '../styles/HowItWorksSection.css';

const steps = [
  {
    num: '1',
    title: 'Upload Receipt',
    desc: 'Drag & drop or browse PNG, JPG, JPEG, or PDF files. Single or batch upload with instant preview.'
  },
  {
    num: '2',
    title: 'AI Extraction',
    desc: 'Gemini AI reads vendor, amount, tax, date, and line items. OCR fallback ensures every receipt is captured.'
  },
  {
    num: '3',
    title: 'Validate & Sync',
    desc: 'Auto-validation checks for duplicates and compliance. Sync to your ERP or export in any format.'
  }
];

const HowItWorksSection = () => {
  return (
    <section className="how-section" id="how">
      <div className="section-header">
        <ScrollReveal>
          <div className="section-tag">Simple Process</div>
        </ScrollReveal>
        <ScrollReveal delay={1}>
          <h2 className="section-title-main">
            Three Steps to<br />
            <span className="gradient-text">Expense Clarity</span>
          </h2>
        </ScrollReveal>
      </div>

      <div className="steps-container">
        {steps.map((step, i) => (
          <ScrollReveal key={i} delay={i + 1}>
            <div className="step">
              <div className="step-num">{step.num}</div>
              <h4>{step.title}</h4>
              <p>{step.desc}</p>
            </div>
          </ScrollReveal>
        ))}
      </div>
    </section>
  );
};

export default HowItWorksSection;
