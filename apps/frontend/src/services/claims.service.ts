import { apiClient } from "./client";
import {
  AddClaimEvidenceRequest,
  Claim,
  ClaimEvidence,
  CreateClaimRequest,
  PaginationParams,
  UUID,
} from "../types";

export type ListClaimsParams = PaginationParams & {
  event_id?: UUID;
};

export const claimsService = {
  async listClaims(params?: ListClaimsParams): Promise<Claim[]> {
    return apiClient.get<Claim[]>("/api/v1/claims", params);
  },

  async getClaim(claimId: UUID): Promise<Claim> {
    return apiClient.get<Claim>(`/api/v1/claims/${claimId}`);
  },

  async createClaim(payload: CreateClaimRequest): Promise<Claim> {
    return apiClient.post<Claim>("/api/v1/claims", payload);
  },

  async getClaimEvidence(claimId: UUID): Promise<ClaimEvidence[]> {
    return apiClient.get<ClaimEvidence[]>(`/api/v1/claims/${claimId}/evidence`);
  },

  async addClaimEvidence(claimId: UUID, payload: AddClaimEvidenceRequest): Promise<ClaimEvidence> {
    return apiClient.post<ClaimEvidence>(`/api/v1/claims/${claimId}/evidence`, payload);
  },
};
