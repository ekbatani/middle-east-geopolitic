import { apiClient } from "./client";
import {
  ModelReviewResult,
  ModelReviewSubjectType,
  PaginationParams,
  UUID,
} from "../types";

export type ListModelReviewsParams = PaginationParams & {
  subject_type?: ModelReviewSubjectType;
  agreement?: boolean;
  since?: string;
};

export const modelReviewsService = {
  async listModelReviews(params?: ListModelReviewsParams): Promise<ModelReviewResult[]> {
    return apiClient.get<ModelReviewResult[]>("/api/v1/model-reviews", params);
  },

  async getModelReview(reviewId: UUID): Promise<ModelReviewResult> {
    return apiClient.get<ModelReviewResult>(`/api/v1/model-reviews/${reviewId}`);
  },
};
