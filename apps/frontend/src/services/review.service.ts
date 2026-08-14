import { apiClient } from "./client";
import {
  AcknowledgeReviewItemRequest,
  PaginationParams,
  ResolveReviewItemRequest,
  ReviewItem,
  ReviewStatus,
  ReviewType,
  UUID,
} from "../types";

export type ListReviewItemsParams = PaginationParams & {
  review_type?: ReviewType;
  status?: ReviewStatus;
};

export const reviewService = {
  async listPending(params?: ListReviewItemsParams): Promise<ReviewItem[]> {
    return apiClient.get<ReviewItem[]>("/api/v1/review-items", params);
  },

  async getReviewItem(itemId: UUID): Promise<ReviewItem> {
    return apiClient.get<ReviewItem>(`/api/v1/review-items/${itemId}`);
  },

  async resolveEntityResolution(
    itemId: UUID,
    payload: ResolveReviewItemRequest
  ): Promise<ReviewItem> {
    return apiClient.post<ReviewItem>(`/api/v1/review-items/${itemId}/resolve`, payload);
  },

  async acknowledgeHighImpactEvent(
    itemId: UUID,
    payload?: AcknowledgeReviewItemRequest
  ): Promise<ReviewItem> {
    return apiClient.post<ReviewItem>(
      `/api/v1/review-items/${itemId}/acknowledge`,
      payload || {}
    );
  },

  async rejectReviewItem(itemId: UUID): Promise<ReviewItem> {
    return apiClient.post<ReviewItem>(`/api/v1/review-items/${itemId}/reject`);
  },
};
