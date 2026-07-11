import React, { useEffect, useRef } from 'react';
import '../styles/AmbientBackground.css';

const AmbientBackground = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let w, h;
    let animId;

    const resize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const stars = Array.from({ length: 80 }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      r: Math.random() * 1.5 + 0.5,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      alpha: Math.random() * 0.5 + 0.2,
    }));

    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      stars.forEach(s => {
        s.x += s.vx; s.y += s.vy;
        if (s.x < 0) s.x = w; if (s.x > w) s.x = 0;
        if (s.y < 0) s.y = h; if (s.y > h) s.y = 0;
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(139, 92, 246, ${s.alpha})`;
        ctx.fill();
      });
      animId = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <>
      <canvas ref={canvasRef} id="ambientCanvas" />
      <div className="noise-overlay" />
      <div className="orb orb-1" />
      <div className="orb orb-2" />
      <div className="orb orb-3" />
      <div className="orb orb-4" />
      <div className="particles-container" id="particlesContainer">
        {Array.from({ length: 30 }).map((_, i) => {
          const size = 3 + Math.random() * 6;
          const dur = 12 + Math.random() * 15;
          const delay = -(Math.random() * 15);
          const maxOp = 0.3 + Math.random() * 0.4;
          return (
            <div
              key={i}
              className="particle"
              style={{
                width: size,
                height: size,
                left: `${Math.random() * 100}%`,
                '--dur': `${dur}s`,
                '--delay': `${delay}s`,
                '--max-op': maxOp,
              }}
            />
          );
        })}
      </div>
    </>
  );
};

export default AmbientBackground;
