"use client";

import { useEffect, useRef } from "react";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface Vec2 {
  x: number;
  y: number;
}

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;    // 0→1  (1 = just born)
  size: number;
  hue: number;
  alpha: number;
}

interface Ripple {
  x: number;
  y: number;
  life: number;   // 0→1
  maxRadius: number;
}

/* ------------------------------------------------------------------ */
/*  Config                                                             */
/* ------------------------------------------------------------------ */

const CFG = {
  // Cursor
  cursorLerp:       0.12,
  cursorDotRadius:  4,
  cursorRingRadius: 14,
  ringExpandOnHover: 8,

  // Glow
  glowBaseRadius:   120,
  glowHoverRadius:  180,

  // Particles
  maxParticles:     80,
  particleLifespan: 1.2,      // seconds
  spawnRate:        2,         // per frame while moving
  particleSpeed:    0.6,
  particleMinSize:  1,
  particleMaxSize:  3,

  // Click ripple
  rippleMaxRadius:  60,
  rippleDuration:   0.5,
  rippleBurstCount: 12,

  // Colors (matches brand-500: #3466ff)
  hue:              225,
  hueVariance:      20,
};

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

function rand(min: number, max: number) {
  return Math.random() * (max - min) + min;
}

const INTERACTIVE_SELECTOR =
  'a, button, input, textarea, select, [role="button"], label, ' +
  '[data-slot="tab"], .spotlight-card, nav a, header button';

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function AICursor() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    // --- Guard: mobile / touch / reduced-motion ---
    const isMobile =
      typeof navigator !== "undefined" &&
      ("ontouchstart" in navigator || navigator.maxTouchPoints > 0);
    if (isMobile) return;

    const prefersReduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReduced) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // --- Sizing ---
    let w = window.innerWidth;
    let h = window.innerHeight;
    const dpr = window.devicePixelRatio || 1;

    function resize() {
      w = window.innerWidth;
      h = window.innerHeight;
      if (canvas && ctx) {
        canvas.width = w * dpr;
        canvas.height = h * dpr;
        canvas.style.width = w + "px";
        canvas.style.height = h + "px";
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      }
    }
    resize();
    window.addEventListener("resize", resize);

    // --- State (all refs, zero React renders) ---
    const mouse:   Vec2 = { x: -100, y: -100 };
    const smooth:   Vec2 = { x: -100, y: -100 };
    const velocity: Vec2 = { x: 0, y: 0 };
    let prevMouse:  Vec2 = { x: -100, y: -100 };
    let isHovering  = false;
    let isUploading = false;
    let isAtsCard   = false;
    let pulse       = 0;
    let particles:  Particle[] = [];
    let ripples:    Ripple[]   = [];

    // --- Event handlers ---
    function onMouseMove(e: MouseEvent) {
      prevMouse.x = mouse.x;
      prevMouse.y = mouse.y;
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    }

    function onMouseDown(e: MouseEvent) {
      // Ripple
      ripples.push({
        x: e.clientX,
        y: e.clientY,
        life: 0,
        maxRadius: CFG.rippleMaxRadius,
      });
      // Burst particles
      for (let i = 0; i < CFG.rippleBurstCount; i++) {
        const angle = (Math.PI * 2 * i) / CFG.rippleBurstCount + rand(-0.3, 0.3);
        const speed = rand(1.5, 4);
        spawnParticle(
          e.clientX + rand(-2, 2),
          e.clientY + rand(-2, 2),
          Math.cos(angle) * speed,
          Math.sin(angle) * speed,
          rand(1.5, 3),
          CFG.hue + rand(-CFG.hueVariance, CFG.hueVariance),
          1
        );
      }
    }

    function onMouseOver(e: MouseEvent) {
      const target = e.target as HTMLElement | null;
      if (!target) return;
      isHovering = !!target.closest(INTERACTIVE_SELECTOR);
      // Detect upload area
      isUploading = !!target.closest(
        'input[type="file"], [class*="upload"], [class*="drop"]'
      );
      // Detect ATS card
      isAtsCard = !!target.closest('[class*="ats"], [class*="ATS"], [class*="score"]');
    }

    function onMouseLeave() {
      isHovering = false;
      isUploading = false;
      isAtsCard = false;
    }

    window.addEventListener("mousemove", onMouseMove, { passive: true });
    window.addEventListener("mousedown", onMouseDown, { passive: true });
    window.addEventListener("mouseover", onMouseOver, { passive: true });
    window.addEventListener("mouseleave", onMouseLeave);

    // Hide default cursor via class (covers dynamically added elements too)
    document.documentElement.classList.add("ai-cursor-active");

    // --- Particle spawning ---
    function spawnParticle(
      x: number, y: number,
      vx: number, vy: number,
      size: number, hue: number, alpha: number
    ) {
      if (particles.length >= CFG.maxParticles) {
        // Recycle oldest
        particles.shift();
      }
      particles.push({
        x, y, vx, vy,
        life: 1,
        size,
        hue,
        alpha,
      });
    }

    // --- Animation loop ---
    let raf = 0;
    let lastTime = performance.now();

    function frame(now: number) {
      const dt = Math.min((now - lastTime) / 1000, 0.05); // cap at 50ms
      lastTime = now;

      if (!ctx) return;
      ctx.clearRect(0, 0, w, h);

      // --- Smooth cursor follow ---
      smooth.x = lerp(smooth.x, mouse.x, CFG.cursorLerp);
      smooth.y = lerp(smooth.y, mouse.y, CFG.cursorLerp);
      velocity.x = mouse.x - smooth.x;
      velocity.y = mouse.y - smooth.y;

      // --- Pulse ---
      pulse += dt * 2.5;
      const pulseAmt = Math.sin(pulse) * 0.15 + 1;

      // --- Cursor sizes ---
      const ringR = (CFG.cursorRingRadius + (isHovering ? CFG.ringExpandOnHover : 0)) * pulseAmt;
      const dotR  = CFG.cursorDotRadius * pulseAmt;

      // --- Glow ---
      const glowR = isHovering ? CFG.glowHoverRadius : CFG.glowBaseRadius;
      const glowAlpha = isHovering ? 0.18 : 0.10;

      const grd = ctx.createRadialGradient(smooth.x, smooth.y, 0, smooth.x, smooth.y, glowR);
      grd.addColorStop(0, `hsla(${CFG.hue}, 80%, 60%, ${glowAlpha})`);
      grd.addColorStop(0.5, `hsla(${CFG.hue}, 70%, 55%, ${glowAlpha * 0.4})`);
      grd.addColorStop(1, `hsla(${CFG.hue}, 60%, 50%, 0)`);
      ctx.fillStyle = grd;
      ctx.beginPath();
      ctx.arc(smooth.x, smooth.y, glowR, 0, Math.PI * 2);
      ctx.fill();

      // Upload area special glow
      if (isUploading) {
        const uGrd = ctx.createRadialGradient(smooth.x, smooth.y, 0, smooth.x, smooth.y, glowR * 1.4);
        uGrd.addColorStop(0, `hsla(${CFG.hue}, 90%, 65%, 0.22)`);
        uGrd.addColorStop(1, `hsla(${CFG.hue}, 60%, 50%, 0)`);
        ctx.fillStyle = uGrd;
        ctx.beginPath();
        ctx.arc(smooth.x, smooth.y, glowR * 1.4, 0, Math.PI * 2);
        ctx.fill();
      }

      // ATS card subtle orbit particles (spawn occasionally)
      if (isAtsCard && Math.random() < 0.15) {
        const angle = rand(0, Math.PI * 2);
        const dist = rand(30, 70);
        spawnParticle(
          smooth.x + Math.cos(angle) * dist,
          smooth.y + Math.sin(angle) * dist,
          Math.cos(angle + Math.PI / 2) * 0.4,
          Math.sin(angle + Math.PI / 2) * 0.4,
          rand(1, 2),
          CFG.hue + rand(-10, 10),
          0.6
        );
      }

      // --- Spawn trail particles ---
      const dx = mouse.x - prevMouse.x;
      const dy = mouse.y - prevMouse.y;
      const speed = Math.sqrt(dx * dx + dy * dy);
      if (speed > 1.5) {
        const count = Math.min(CFG.spawnRate, Math.ceil(speed / 8));
        for (let i = 0; i < count; i++) {
          const t = i / count;
          const px = lerp(prevMouse.x, mouse.x, t) + rand(-3, 3);
          const py = lerp(prevMouse.y, mouse.y, t) + rand(-3, 3);
          const spread = isUploading ? 1.8 : 1;
          spawnParticle(
            px, py,
            rand(-CFG.particleSpeed, CFG.particleSpeed) * spread,
            rand(-CFG.particleSpeed, CFG.particleSpeed) * spread - (isUploading ? 0.8 : 0),
            rand(CFG.particleMinSize, CFG.particleMaxSize) * (isHovering ? 1.3 : 1),
            CFG.hue + rand(-CFG.hueVariance, CFG.hueVariance),
            rand(0.5, 0.9)
          );
        }
      }

      // --- Update & draw particles ---
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.life -= dt / CFG.particleLifespan;
        if (p.life <= 0) {
          particles.splice(i, 1);
          continue;
        }
        p.x += p.vx;
        p.y += p.vy;
        p.vx *= 0.97;
        p.vy *= 0.97;

        const a = p.life * p.alpha;
        const sz = p.size * (0.4 + p.life * 0.6);

        // Glow
        ctx.beginPath();
        ctx.arc(p.x, p.y, sz * 3, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${p.hue}, 80%, 65%, ${a * 0.2})`;
        ctx.fill();

        // Core
        ctx.beginPath();
        ctx.arc(p.x, p.y, sz, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${p.hue}, 80%, 75%, ${a})`;
        ctx.fill();
      }

      // --- Update & draw ripples ---
      for (let i = ripples.length - 1; i >= 0; i--) {
        const r = ripples[i];
        r.life += dt / CFG.rippleDuration;
        if (r.life >= 1) {
          ripples.splice(i, 1);
          continue;
        }
        const t = r.life;
        const radius = t * r.maxRadius;
        const alpha = (1 - t) * 0.5;

        ctx.beginPath();
        ctx.arc(r.x, r.y, radius, 0, Math.PI * 2);
        ctx.strokeStyle = `hsla(${CFG.hue}, 80%, 65%, ${alpha})`;
        ctx.lineWidth = 1.5 * (1 - t);
        ctx.stroke();
      }

      // --- Draw cursor ring ---
      ctx.beginPath();
      ctx.arc(smooth.x, smooth.y, ringR, 0, Math.PI * 2);
      ctx.strokeStyle = `hsla(${CFG.hue}, 80%, 70%, ${isHovering ? 0.7 : 0.45})`;
      ctx.lineWidth = isHovering ? 2 : 1.5;
      ctx.stroke();

      // --- Draw cursor dot ---
      ctx.beginPath();
      ctx.arc(smooth.x, smooth.y, dotR, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${CFG.hue}, 85%, 75%, 0.95)`;
      ctx.fill();

      raf = requestAnimationFrame(frame);
    }

    raf = requestAnimationFrame(frame);

    // --- Cleanup ---
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mouseover", onMouseOver);
      window.removeEventListener("mouseleave", onMouseLeave);
      document.documentElement.classList.remove("ai-cursor-active");
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none fixed inset-0"
      style={{ zIndex: 99999 }}
    />
  );
}
