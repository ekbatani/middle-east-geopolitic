"use client";

import { useEffect, useState } from "react";
import Image from "next/image";

type HealthStatus = {
  status: string;
};

function getNormalizedApiUrl(rawUrl?: string): string {
  let url = (rawUrl || "http://localhost:8000").trim();
  if (!url) return "http://localhost:8000";
  if (!/^https?:\/\//i.test(url) && !url.startsWith("/")) {
    url = `http://${url}`;
  }
  return url;
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_URL = getNormalizedApiUrl(process.env.NEXT_PUBLIC_API_URL);

  useEffect(() => {
    async function checkHealth() {
      try {
        const url = API_URL.endsWith('/') ? `${API_URL}health/live` : `${API_URL}/health/live`;
        const res = await fetch(url);
        if (!res.ok) {
          throw new Error(`API request failed with status: ${res.status}`);
        }
        const data = await res.json();
        setHealth(data);
        setError(null);
      } catch (err) {
        console.error("Health check error:", err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    checkHealth();
  }, [API_URL]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 py-4 px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Image
            src="/logo.png"
            alt="MEI Logo"
            width={40}
            height={40}
            className="h-10 w-auto object-contain"
            priority
          />
          <h1 className="text-xl font-bold text-gray-900">
            Middle East Geopolitical Intelligence Platform
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">API Status:</span>
          {loading ? (
            <span className="h-2 w-2 rounded-full bg-yellow-400 animate-pulse"></span>
          ) : error ? (
            <span
              className="h-2 w-2 rounded-full bg-red-500"
              title={error}
            ></span>
          ) : (
            <span
              className="h-2 w-2 rounded-full bg-green-500"
              title={health?.status}
            ></span>
          )}
        </div>
      </header>

      <div className="flex flex-1">
        <aside className="w-64 bg-white border-r border-gray-200 p-4">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-gray-100">
            <Image
              src="/logo.png"
              alt="MEI Logo"
              width={28}
              height={28}
              className="h-7 w-auto object-contain"
            />
            <span className="font-semibold text-gray-800 text-sm">Navigation</span>
          </div>
          <nav className="flex flex-col gap-2">
            <a
              href="#"
              className="p-2 rounded hover:bg-gray-100 text-gray-700 font-medium"
            >
              Dashboard
            </a>
            <a
              href="#"
              className="p-2 rounded hover:bg-gray-100 text-gray-700 font-medium"
            >
              Reports
            </a>
            <a
              href="#"
              className="p-2 rounded hover:bg-gray-100 text-gray-700 font-medium"
            >
              Sources
            </a>
            <a
              href="#"
              className="p-2 rounded hover:bg-gray-100 text-gray-700 font-medium"
            >
              Actors
            </a>
            <a
              href="#"
              className="p-2 rounded hover:bg-gray-100 text-gray-700 font-medium"
            >
              Investigations
            </a>
          </nav>
        </aside>

        <main className="flex-1 p-8">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-semibold mb-6">
              Welcome to MEI Interface
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-medium mb-2">Backend Connection</h3>
                <div className="text-sm text-gray-600 mb-4">
                  Currently connected to:{" "}
                  <code className="bg-gray-100 px-1 py-0.5 rounded">
                    {API_URL}
                  </code>
                </div>

                {loading ? (
                  <div className="text-gray-500">Connecting to API...</div>
                ) : error ? (
                  <div className="text-red-500 border border-red-200 bg-red-50 p-3 rounded">
                    <strong>Connection Error:</strong> {error}
                  </div>
                ) : (
                  <div className="text-green-600 border border-green-200 bg-green-50 p-3 rounded">
                    <strong>Connected successfully:</strong> API is{" "}
                    {health?.status}
                  </div>
                )}
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-medium mb-2">Getting Started</h3>
                <p className="text-gray-600 mb-4">
                  This frontend allows interaction with the MEI backend directly.
                  Navigate through the sidebar to explore intelligence data.
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
