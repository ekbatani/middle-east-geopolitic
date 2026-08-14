"use client";

import React, { useState } from "react";
import { Modal } from "./Modal";
import { useAuth } from "../../context/AuthContext";
import { KeyIcon, CheckCircleIcon, ShieldIcon, ActivityIcon } from "./Icons";
import { Badge } from "./Badge";

type AuthModalProps = {
  isOpen: boolean;
  onClose: () => void;
};

export function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const { apiKey, scopes, isAuthenticated, loginWithApiKey, logout } = useAuth();
  const [inputKey, setInputKey] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [msg, setMsg] = useState<{ text: string; type: "success" | "error" } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputKey.trim()) return;

    setIsSubmitting(true);
    setMsg(null);
    try {
      const success = await loginWithApiKey(inputKey.trim());
      if (success) {
        setMsg({ text: "Authentication successful! Access granted.", type: "success" });
        setInputKey("");
        setTimeout(() => {
          onClose();
        }, 1200);
      }
    } catch (err: any) {
      setMsg({
        text: err?.message || "Authentication failed. Please check your key.",
        type: "error",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Analyst Authentication & API Access"
      subtitle="Configure bearer credentials for scoped analytical operations"
      maxWidth="md"
    >
      <div className="space-y-5">
        {isAuthenticated ? (
          <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-800/40 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-emerald-300 font-medium text-sm">
                <CheckCircleIcon className="w-5 h-5 text-emerald-400" />
                Active Session Authenticated
              </div>
              <button
                onClick={logout}
                className="text-xs px-2.5 py-1 rounded bg-rose-900/50 hover:bg-rose-900 text-rose-200 border border-rose-800/50 transition"
              >
                Disconnect
              </button>
            </div>
            <div className="text-xs text-slate-300">
              <span className="text-slate-400">Current Key:</span>{" "}
              <code className="bg-slate-900 px-1.5 py-0.5 rounded text-emerald-400">
                {apiKey ? `${apiKey.slice(0, 8)}...${apiKey.slice(-4)}` : "JWT Token"}
              </code>
            </div>

            {scopes.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-400 mb-1.5 flex items-center gap-1">
                  <ShieldIcon className="w-3.5 h-3.5" /> Assigned Scopes:
                </p>
                <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
                  {scopes.map((s) => (
                    <Badge key={s} variant="info" size="sm">
                      {s}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                API Key or Bearer Token
              </label>
              <div className="relative">
                <input
                  type="password"
                  placeholder="mei_live_..."
                  value={inputKey}
                  onChange={(e) => setInputKey(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition font-mono"
                  required
                />
                <KeyIcon className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Provide your analyst key (`mei_...`) or JWT token to enable restricted actions like approving events, recalculating risks, and launching investigations.
              </p>
            </div>

            {msg && (
              <div
                className={`p-3 rounded-lg text-xs font-medium ${
                  msg.type === "success"
                    ? "bg-emerald-950/60 text-emerald-300 border border-emerald-800"
                    : "bg-rose-950/60 text-rose-300 border border-rose-800"
                }`}
              >
                {msg.text}
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || !inputKey.trim()}
                className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-xs font-semibold text-white transition flex items-center gap-1.5"
              >
                {isSubmitting ? (
                  <>
                    <ActivityIcon className="w-3.5 h-3.5 animate-spin" /> Verifying...
                  </>
                ) : (
                  "Authenticate"
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </Modal>
  );
}
