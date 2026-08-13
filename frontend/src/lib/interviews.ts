import "server-only";

import { backendFetch } from "@/lib/backend-api";

export type InterviewType = "behavioral" | "technical" | "mixed";
export type InterviewDifficulty = "introductory" | "intermediate" | "advanced";
export type InterviewStatus = "active" | "completed" | "abandoned";

export type InterviewHighlight = {
  title: string;
  detail: string;
};

export type TurnFeedback = {
  score: number;
  strengths: string;
  improvement: string;
};

export type InterviewTurn = {
  id: string;
  sequence_number: number;
  question: string;
  answer: string | null;
  /** Empty until the turn is answered and scored. */
  feedback: Partial<TurnFeedback>;
  created_at: string;
  updated_at: string;
};

export type InterviewSession = {
  id: string;
  target_role: string;
  interview_type: InterviewType;
  difficulty: InterviewDifficulty;
  question_limit: number;
  status: InterviewStatus;
  summary: string | null;
  strengths: InterviewHighlight[];
  improvements: InterviewHighlight[];
  learning_recommendations: InterviewHighlight[];
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type InterviewSessionWithTurns = InterviewSession & {
  turns: InterviewTurn[];
};

export class InterviewError extends Error {}

async function responseError(response: Response, fallback: string) {
  try {
    const error = (await response.json()) as { detail?: string };
    return error.detail ?? fallback;
  } catch {
    return fallback;
  }
}

export async function getInterviewSessions(): Promise<InterviewSession[] | null> {
  try {
    const response = await backendFetch("/interviews", { cache: "no-store" });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export async function getInterviewSession(
  sessionId: string,
): Promise<InterviewSessionWithTurns | null> {
  try {
    const response = await backendFetch(`/interviews/${sessionId}`, {
      cache: "no-store",
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export async function createInterviewSession(
  targetRole: string,
  interviewType: InterviewType,
  difficulty: InterviewDifficulty,
  questionLimit: number,
): Promise<InterviewSessionWithTurns> {
  const response = await backendFetch("/interviews", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      target_role: targetRole,
      interview_type: interviewType,
      difficulty,
      question_limit: questionLimit,
    }),
  });

  if (!response.ok) {
    if (response.status === 502) {
      throw new InterviewError(
        "The mock interviewer is unavailable right now. Make sure ANTHROPIC_API_KEY is set on the backend.",
      );
    }
    throw new InterviewError(
      await responseError(response, "FastAPI could not start the interview."),
    );
  }
  return response.json();
}

export async function submitInterviewAnswer(
  sessionId: string,
  answer: string,
): Promise<InterviewSessionWithTurns> {
  const response = await backendFetch(`/interviews/${sessionId}/answers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answer }),
  });

  if (!response.ok) {
    if (response.status === 502) {
      throw new InterviewError(
        "The mock interviewer is unavailable right now. Make sure ANTHROPIC_API_KEY is set on the backend.",
      );
    }
    throw new InterviewError(
      await responseError(response, "FastAPI could not submit the answer."),
    );
  }
  return response.json();
}
