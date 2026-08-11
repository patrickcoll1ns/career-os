"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import {
  createResumeReview,
  ResumeReviewError,
} from "@/lib/resume-reviews";

export type ResumeReviewFormState = {
  status: "idle" | "error";
  message: string;
};

export async function createResumeReviewAction(
  _previousState: ResumeReviewFormState,
  formData: FormData,
): Promise<ResumeReviewFormState> {
  const documentId = String(formData.get("documentId") ?? "").trim();
  const targetRole = String(formData.get("targetRole") ?? "").trim();

  if (!documentId) {
    return { status: "error", message: "Choose an indexed resume to review." };
  }
  if (targetRole.length > 200) {
    return { status: "error", message: "Target role must be 200 characters or less." };
  }

  let reviewId: string;
  try {
    const review = await createResumeReview(documentId, targetRole || undefined);
    reviewId = review.id;
  } catch (error) {
    return {
      status: "error",
      message:
        error instanceof ResumeReviewError
          ? error.message
          : "Could not generate the review. Make sure FastAPI is running.",
    };
  }

  revalidatePath("/resume-reviews");
  redirect(`/resume-reviews/${reviewId}`);
}
