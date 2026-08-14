import { apiClient, getNormalizedApiUrl, getStoredAuth } from "./client";
import {
  ImageEvidence,
  LinkImageToBundleRequest,
  PaginationParams,
  SubmitImageRequest,
  UUID,
  VerificationStatus,
} from "../types";

export type ListImagesParams = PaginationParams & {
  source_id?: UUID;
  verification_status?: VerificationStatus;
  since?: string;
  until?: string;
};

export const imageryService = {
  async listImages(params?: ListImagesParams): Promise<ImageEvidence[]> {
    return apiClient.get<ImageEvidence[]>("/api/v1/imagery", params);
  },

  async getImage(imageId: UUID): Promise<ImageEvidence> {
    return apiClient.get<ImageEvidence>(`/api/v1/imagery/${imageId}`);
  },

  getRawImageUrl(imageId: UUID): string {
    const baseUrl = getNormalizedApiUrl();
    const stored = getStoredAuth();
    // Raw endpoint URL
    const url = new URL(`${baseUrl}/api/v1/imagery/${imageId}/raw`);
    if (stored.token) {
      url.searchParams.append("token", stored.token);
    }
    return url.toString();
  },

  async submitImage(payload: SubmitImageRequest): Promise<ImageEvidence> {
    return apiClient.post<ImageEvidence>("/api/v1/imagery/submit", payload);
  },

  async reanalyzeImage(imageId: UUID): Promise<ImageEvidence> {
    return apiClient.post<ImageEvidence>(`/api/v1/imagery/${imageId}/analyze`);
  },

  async linkToBundle(
    imageId: UUID,
    payload: LinkImageToBundleRequest
  ): Promise<{ bundle_id: UUID; image_evidence_id: UUID }> {
    return apiClient.post<{ bundle_id: UUID; image_evidence_id: UUID }>(
      `/api/v1/imagery/${imageId}/link-to-bundle`,
      payload
    );
  },
};
