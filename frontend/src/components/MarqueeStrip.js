import React from 'react';
import '../styles/MarqueeStrip.css';

const items = [
  'GEMINI AI EXTRACTION', 'OCR FALLBACK ENGINE', 'REAL-TIME VALIDATION',
  'DUPLICATE DETECTION', 'ERP INTEGRATION', 'TAX COMPLIANCE',
  'SPEND ANALYTICS', 'MULTI-LANGUAGE'
];

const MarqueeStrip = () => {
  const content = [...items, ...items];
  return (
    <div className="marquee-strip">
      <div className="marquee-content">
        {content.map((item, i) => (
          <span key={i}>{item}</span>
        ))}
      </div>
    </div>
  );
};

export default MarqueeStrip;
