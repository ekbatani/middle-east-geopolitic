import React from "react";
import { AlertTriangleIcon, RadarIcon, RefreshCwIcon } from "./Icons";

export function LoadingState({ message = "Analyzing intelligence data..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <div className="relative flex items-center justify-center mb-4">
        <RadarIcon className="w-10 h-10 text-sky-400 animate-spin" />
        <span className="absolute w-14 h-14 rounded-full border border-sky-500/30 animate-ping" />
      </div>
      <p className="text-sm font-medium text-slate-300">{message}</p>
      <p className="text-xs text-slate-500 mt-1">Connecting to FastAPI engine</p>
    </div>
  );
}

export function ErrorState({
  message = "Failed to load intelligence records",
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 bg-rose-950/20 border border-rose-900/40 rounded-xl text-center">
      <AlertTriangleIcon className="w-8 h-8 text-rose-400 mb-3" />
      <h4 className="text-sm font-semibold text-rose-200">System Error</h4>
      <p className="text-xs text-rose-300/80 mt-1 max-w-md">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-900/60 hover:bg-rose-800 text-xs font-medium text-rose-100 transition border border-rose-700/50"
        >
          <RefreshCwIcon className="w-3.5 h-3.5" />
          Retry Request
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  title = "No intelligence items found",
  description = "No matching records were found for the selected query or filter criteria.",
  action,
}: {
  title?: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-12 border border-dashed border-slate-800 rounded-xl text-center bg-slate-950/30">
      <div className="p-3 rounded-full bg-slate-900 border border-slate-800 text-slate-400 mb-3">
        <RadarIcon className="w-6 h-6" />
      </div>
      <h4 className="text-sm font-semibold text-slate-200">{title}</h4>
      <p className="text-xs text-slate-400 mt-1 max-w-sm">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
