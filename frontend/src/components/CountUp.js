import React, { useEffect, useRef, useState } from 'react';

const CountUp = ({ target, suffix = '', duration = 2000 }) => {
  const [value, setValue] = useState(0);
  const ref = useRef(null);
  const hasAnimated = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasAnimated.current) {
            hasAnimated.current = true;
            const start = performance.now();
            const isFloat = target % 1 !== 0;

            const update = (now) => {
              const elapsed = now - start;
              const progress = Math.min(elapsed / duration, 1);
              const eased = 1 - Math.pow(1 - progress, 3);
              const cur = isFloat ? (target * eased).toFixed(1) : Math.round(target * eased);
              setValue(cur);
              if (progress < 1) requestAnimationFrame(update);
            };
            requestAnimationFrame(update);
            observer.unobserve(el);
          }
        });
      },
      { threshold: 0.5 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [target, suffix, duration]);

  return (
    <span ref={ref}>
      {value}{suffix}
    </span>
  );
};

export default CountUp;
