import React from "react";

type CardProps = {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hover?: boolean;
};

export function Card({ children, className = "", onClick, hover = false }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={`bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm transition ${
        hover ? "hover:border-slate-700 hover:bg-slate-900 cursor-pointer hover:shadow-md" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
}

type CardHeaderProps = {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
};

export function CardHeader({ title, subtitle, action, icon }: CardHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-4 mb-4 pb-3 border-b border-slate-800/60">
      <div className="flex items-center gap-3">
        {icon && <div className="p-2 rounded-lg bg-slate-800/80 text-sky-400">{icon}</div>}
        <div>
          <h3 className="font-semibold text-slate-100 text-base">{title}</h3>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {action && <div className="flex items-center gap-2">{action}</div>}
    </div>
  );
}
