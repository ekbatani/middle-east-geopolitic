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
          .catch((err) => {
            console.warn("Could not exchange stored API key for JWT token:", err);
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
    try {
      const res = await authService.exchangeToken(key);
      startTransition(() => {
        setApiKey(key);
        setJwtToken(res.access_token);
        setScopes(res.scopes);
        setStoredAuth(res.access_token, key);
      });
      return true;
    } catch (err) {
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
