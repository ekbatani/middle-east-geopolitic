"use client";

import React, { createContext, useContext, useEffect, useState, useTransition } from "react";
import { getStoredAuth, setStoredAuth } from "../services/client";
import { authService } from "../services/auth.service";

type AuthContextType = {
  apiKey: string | null;
  jwtToken: string | null;
  scopes: string[];
  isAuthenticated: boolean;
  isLoading: boolean;
  loginWithApiKey: (key: string) => Promise<boolean>;
  logout: () => void;
  hasScope: (scope: string) => boolean;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [jwtToken, setJwtToken] = useState<string | null>(null);
  const [scopes, setScopes] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [, startTransition] = useTransition();

  useEffect(() => {
    const stored = getStoredAuth();
    if (stored.apiKey || stored.token) {
      if (stored.apiKey && !stored.apiKey.startsWith("mei_")) {
        setStoredAuth(null, null);
        setApiKey(null);
        setJwtToken(null);
        setIsLoading(false);
        return;
      }
      setApiKey(stored.apiKey);
      setJwtToken(stored.token);
      if (stored.apiKey) {
        // Attempt exchange in background to refresh scopes
        authService
          .exchangeToken(stored.apiKey)
          .then((res) => {
            setJwtToken(res.access_token);
            setScopes(res.scopes);
            setStoredAuth(res.access_token, stored.apiKey);
          })
          .catch((err: any) => {
            console.warn("Could not exchange stored API key for JWT token:", err);
            if (err?.status === 401 || err?.status === 403) {
              setStoredAuth(null, null);
              setApiKey(null);
              setJwtToken(null);
            }
          })
          .finally(() => {
            setIsLoading(false);
          });
      } else {
        setIsLoading(false);
      }
    } else {
      setIsLoading(false);
    }
  }, []);

  const loginWithApiKey = async (key: string): Promise<boolean> => {
    if (!key.startsWith("mei_")) {
      throw new Error("Invalid API key format. API keys must start with 'mei_' (UUIDs or key IDs cannot be used).");
    }
    try {
      const res = await authService.exchangeToken(key);
      startTransition(() => {
        setApiKey(key);
        setJwtToken(res.access_token);
        setScopes(res.scopes);
        setStoredAuth(res.access_token, key);
      });
      return true;
    } catch (err: any) {
      if (err?.status === 401 || err?.status === 403) {
        throw new Error("Authentication failed: API key was not recognized or is expired.");
      }
      console.warn("Direct token exchange failed, storing raw API key as bearer:", err);
      // Even if token exchange fails (e.g. mock or backend offline), save API key so requests use Authorization: Bearer <key>
      startTransition(() => {
        setApiKey(key);
        setStoredAuth(null, key);
      });
      return true;
    }
  };

  const logout = () => {
    startTransition(() => {
      setApiKey(null);
      setJwtToken(null);
      setScopes([]);
      setStoredAuth(null, null);
    });
  };

  const hasScope = (scope: string): boolean => {
    if (!scopes.length && (apiKey || jwtToken)) return true; // optimistic if user has credentials
    return scopes.includes(scope);
  };

  return (
    <AuthContext.Provider
      value={{
        apiKey,
        jwtToken,
        scopes,
        isAuthenticated: !!(apiKey || jwtToken),
        isLoading,
        loginWithApiKey,
        logout,
        hasScope,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
