"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import {
  createInterviewSession,
  InterviewError,
  submitInterviewAnswer,
  type InterviewDifficulty,
  type InterviewType,
} from "@/lib/interviews";

const INTERVIEW_TYPES: InterviewType[] = ["behavioral", "technical", "mixed"];
const INTERVIEW_DIFFICULTIES: InterviewDifficulty[] = [
  "introductory",
  "intermediate",
  "advanced",
];

export type InterviewSetupFormState = {
  status: "idle" | "error";
  message: string;
};

export type InterviewAnswerFormState = {
  status: "idle" | "success" | "error";
  message: string;
};

export async function startInterviewAction(
  _previousState: InterviewSetupFormState,
  formData: FormData,
): Promise<InterviewSetupFormState> {
  const targetRole = String(formData.get("targetRole") ?? "").trim();
  const interviewType = String(formData.get("interviewType") ?? "");
  const difficulty = String(formData.get("difficulty") ?? "");
  const questionLimit = Number(formData.get("questionLimit") ?? 5);

  if (!targetRole) {
    return { status: "error", message: "Enter the role you want to practice for." };
  }
  if (!INTERVIEW_TYPES.includes(interviewType as InterviewType)) {
    return { status: "error", message: "Choose an interview type." };
  }
  if (!INTERVIEW_DIFFICULTIES.includes(difficulty as InterviewDifficulty)) {
    return { status: "error", message: "Choose a difficulty." };
  }
  if (!Number.isInteger(questionLimit) || questionLimit < 1 || questionLimit > 20) {
    return { status: "error", message: "Question count must be between 1 and 20." };
  }

  let sessionId: string;
  try {
    const session = await createInterviewSession(
      targetRole,
      interviewType as InterviewType,
      difficulty as InterviewDifficulty,
      questionLimit,
    );
    sessionId = session.id;
  } catch (error) {
    return {
      status: "error",
      message:
        error instanceof InterviewError
          ? error.message
          : "Could not start the interview. Make sure FastAPI is running.",
    };
  }

  revalidatePath("/interviews");
  redirect(`/interviews/${sessionId}`);
}

export async function submitInterviewAnswerAction(
  _previousState: InterviewAnswerFormState,
  formData: FormData,
): Promise<InterviewAnswerFormState> {
  const sessionId = String(formData.get("sessionId") ?? "");
  const answer = String(formData.get("answer") ?? "").trim();

  if (!sessionId || !answer) {
    return { status: "error", message: "Write an answer before submitting." };
  }

  try {
    await submitInterviewAnswer(sessionId, answer);
    revalidatePath(`/interviews/${sessionId}`);
    return { status: "success", message: "" };
  } catch (error) {
    return {
      status: "error",
      message:
        error instanceof InterviewError
          ? error.message
          : "Could not submit the answer.",
    };
  }
}
