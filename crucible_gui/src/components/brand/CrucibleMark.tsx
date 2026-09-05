type CrucibleMarkProps = {
  size?: number;
  className?: string;
};

/**
 * The Crucible brand mark: a pot pouring molten, glowing data.
 * Pure inline SVG so it stays crisp at any size and needs no asset request.
 */
export function CrucibleMark({ size = 32, className }: CrucibleMarkProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      className={className}
      role="img"
      aria-label="Crucible"
    >
      <defs>
        <linearGradient id="crucible-melt" x1="32" y1="14" x2="32" y2="40" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#ffe9a8" />
          <stop offset="35%" stopColor="#ff9d3d" />
          <stop offset="70%" stopColor="#f2600a" />
          <stop offset="100%" stopColor="#b23e08" />
        </linearGradient>
        <radialGradient id="crucible-glow" cx="32" cy="20" r="20" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#ffd48a" stopOpacity="0.9" />
          <stop offset="100%" stopColor="#ffd48a" stopOpacity="0" />
        </radialGradient>
      </defs>

      <circle cx="32" cy="20" r="18" fill="url(#crucible-glow)" />

      <path
        d="M10 16 H54 L48 20 C48 34 41 44 32 44 C23 44 16 34 16 20 Z"
        fill="#101113"
        stroke="#3a3d42"
        strokeWidth="1.5"
      />

      <path
        d="M14 18 H50 C49.4 30 41.8 39 32 39 C22.2 39 14.6 30 14 18 Z"
        fill="url(#crucible-melt)"
      />

      <rect x="8" y="13" width="48" height="5" rx="2.5" fill="#1c1d20" stroke="#45484e" strokeWidth="1" />

      <path
        d="M31 44 C31 47.5 29.5 49 27.5 51"
        stroke="url(#crucible-melt)"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
      <path
        d="M33.4 44 C33.4 48 35.2 49.6 36.5 52.5"
        stroke="url(#crucible-melt)"
        strokeWidth="2"
        strokeLinecap="round"
      />

      <rect x="26" y="53" width="4" height="4" rx="1" fill="#f2600a" />
      <rect x="34" y="55.5" width="3.4" height="3.4" rx="1" fill="#d94e07" />
      <rect x="20" y="55" width="3" height="3" rx="1" fill="#7c2d0f" opacity="0.9" />
    </svg>
  );
}
