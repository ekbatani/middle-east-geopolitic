import { apiClient } from "./client";
import { Document, PaginationParams, UUID } from "../types";

export type ListDocumentsParams = PaginationParams & {
  source_id?: UUID;
};

export const documentsService = {
  async listDocuments(params?: ListDocumentsParams): Promise<Document[]> {
    return apiClient.get<Document[]>("/api/v1/documents", params);
  },

  async getDocument(documentId: UUID): Promise<Document> {
    return apiClient.get<Document>(`/api/v1/documents/${documentId}`);
  },
};
