import React from "react";

type BadgeVariant =
  | "default"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "neutral"
  | "critical"
  | "high"
  | "medium"
  | "low";

type BadgeProps = {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: "sm" | "md";
  className?: string;
};

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-slate-800 text-slate-200 border-slate-700",
  success: "bg-emerald-950/80 text-emerald-300 border-emerald-800/60",
  warning: "bg-amber-950/80 text-amber-300 border-amber-800/60",
  danger: "bg-rose-950/80 text-rose-300 border-rose-800/60",
  info: "bg-sky-950/80 text-sky-300 border-sky-800/60",
  neutral: "bg-slate-900 text-slate-400 border-slate-800",
  critical: "bg-red-950 text-red-200 border-red-700 font-semibold animate-pulse",
  high: "bg-orange-950/80 text-orange-300 border-orange-800/60",
  medium: "bg-amber-950/70 text-amber-300 border-amber-800/50",
  low: "bg-slate-800/80 text-slate-300 border-slate-700",
};

export function Badge({ children, variant = "default", size = "sm", className = "" }: BadgeProps) {
  const sizeStyle = size === "sm" ? "text-xs px-2 py-0.5" : "text-sm px-2.5 py-1";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border font-medium uppercase tracking-wider ${sizeStyle} ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
}

export function SeverityBadge({ severity }: { severity?: number | null }) {
  if (severity === null || severity === undefined) {
    return <Badge variant="neutral">Unrated</Badge>;
  }

  if (severity >= 5) return <Badge variant="critical">CRIT {severity}/5</Badge>;
  if (severity === 4) return <Badge variant="high">HIGH {severity}/5</Badge>;
  if (severity === 3) return <Badge variant="medium">MED {severity}/5</Badge>;
  return <Badge variant="low">LOW {severity}/5</Badge>;
}

export function VerificationBadge({ status }: { status: string }) {
  switch (status.toLowerCase()) {
    case "confirmed":
      return <Badge variant="success">Confirmed</Badge>;
    case "corroborated":
      return <Badge variant="info">Corroborated</Badge>;
    case "unverified":
      return <Badge variant="warning">Unverified</Badge>;
    case "debunked":
    case "disputed":
      return <Badge variant="danger">{status}</Badge>;
    default:
      return <Badge variant="neutral">{status}</Badge>;
  }
}

export function TrendBadge({ trend }: { trend?: string | null }) {
  if (!trend) return null;
  const t = trend.toLowerCase();
  if (t === "rising") {
    return <Badge variant="danger">▲ Rising</Badge>;
  }
  if (t === "falling") {
    return <Badge variant="success">▼ Falling</Badge>;
  }
  return <Badge variant="neutral">━ Stable</Badge>;
}
