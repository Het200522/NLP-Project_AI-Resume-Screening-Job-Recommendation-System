"use client";

import { useRef, useState, useCallback, ReactNode } from "react";

interface SpotlightCardProps {
  children: ReactNode;
  className?: string;
  tiltStrength?: number;
}

export default function SpotlightCard({
  children,
  className = "",
  tiltStrength = 6,
}: SpotlightCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const glowRef = useRef<HTMLDivElement>(null);
  const [hovering, setHovering] = useState(false);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const el = ref.current;
      const glow = glowRef.current;
      if (!el || !glow) return;

      const rect = el.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      glow.style.opacity = "1";
      glow.style.background = `radial-gradient(350px circle at ${x}px ${y}px, rgba(52,102,255,0.18), transparent 70%)`;

      if (tiltStrength > 0) {
        const nx = (x / rect.width) * 2 - 1;
        const ny = (y / rect.height) * 2 - 1;
        el.style.transform = `perspective(800px) rotateX(${ny * -tiltStrength}deg) rotateY(${nx * tiltStrength}deg) scale3d(1.02,1.02,1.02)`;
      }
    },
    [tiltStrength]
  );

  const handleMouseEnter = useCallback(() => setHovering(true), []);

  const handleMouseLeave = useCallback(() => {
    setHovering(false);
    const el = ref.current;
    const glow = glowRef.current;
    if (el) el.style.transform = "perspective(800px) rotateX(0deg) rotateY(0deg) scale3d(1,1,1)";
    if (glow) glow.style.opacity = "0";
  }, []);

  return (
    <div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`relative overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--surface)] transition-shadow duration-300 ${
        hovering ? "shadow-lg shadow-black/10 dark:shadow-black/40" : ""
      } ${className}`}
      style={{ transformStyle: "preserve-3d" }}
    >
      <div
        ref={glowRef}
        className="pointer-events-none absolute inset-0 z-10 opacity-0 transition-opacity duration-200"
        style={{ opacity: 0 }}
      />
      <div className="relative z-20">{children}</div>
    </div>
  );
}
