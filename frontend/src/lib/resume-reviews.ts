import "server-only";

import { backendFetch } from "@/lib/backend-api";

export type ReviewFinding = {
  title: string;
  evidence: string;
  recommendation: string;
};

export type RewriteSuggestion = {
  original: string;
  rewrite: string;
  rationale: string;
};

export type ResumeReview = {
  id: string;
  document_id: string;
  target_role: string | null;
  status: "pending" | "completed" | "failed";
  summary: string | null;
  strengths: ReviewFinding[];
  gaps: ReviewFinding[];
  rewrite_suggestions: RewriteSuggestion[];
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export class ResumeReviewError extends Error {}

async function responseError(response: Response, fallback: string) {
  try {
    const error = (await response.json()) as { detail?: string };
    return error.detail ?? fallback;
  } catch {
    return fallback;
  }
}

export async function getResumeReviews(): Promise<ResumeReview[] | null> {
  try {
    const response = await backendFetch("/resume-reviews", { cache: "no-store" });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export async function getResumeReview(reviewId: string): Promise<ResumeReview | null> {
  try {
    const response = await backendFetch(`/resume-reviews/${reviewId}`, {
      cache: "no-store",
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export async function createResumeReview(
  documentId: string,
  targetRole?: string,
): Promise<ResumeReview> {
  const response = await backendFetch("/resume-reviews", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      document_id: documentId,
      ...(targetRole ? { target_role: targetRole } : {}),
    }),
  });

  if (!response.ok) {
    throw new ResumeReviewError(
      await responseError(response, "FastAPI could not generate the resume review."),
    );
  }
  return response.json();
}
