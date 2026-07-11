import React, { useEffect, useRef } from 'react';
import '../styles/CursorGlow.css';

const CursorGlow = () => {
  const glowRef = useRef(null);

  useEffect(() => {
    const glow = glowRef.current;
    let mouseX = 0, mouseY = 0, cursorX = 0, cursorY = 0;
    let animId;

    const onMove = (e) => { mouseX = e.clientX; mouseY = e.clientY; };
    document.addEventListener('mousemove', onMove);

    const animate = () => {
      cursorX += (mouseX - cursorX) * 0.1;
      cursorY += (mouseY - cursorY) * 0.1;
      glow.style.left = cursorX + 'px';
      glow.style.top = cursorY + 'px';
      animId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      document.removeEventListener('mousemove', onMove);
      cancelAnimationFrame(animId);
    };
  }, []);

  return <div className="cursor-glow" ref={glowRef} />;
};

export default CursorGlow;
