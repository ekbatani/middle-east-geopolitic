import { apiClient } from "./client";
import { TokenResponse } from "../types";

export const authService = {
  /**
   * Exchange an API key (mei_...) for a short-lived JWT access token
   */
  async exchangeToken(apiKey: string): Promise<TokenResponse> {
    return apiClient.post<TokenResponse>(
      "/api/v1/auth/token",
      undefined,
      {
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
      }
    );
  },
};
