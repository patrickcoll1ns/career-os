"use server";

import { revalidatePath } from "next/cache";

import {
  archiveGoal,
  createGoal,
  deleteGoal,
  restoreGoal,
  type GoalHorizon,
  type GoalStatus,
  updateGoalDetails,
  updateGoalStatus,
} from "@/lib/goals";

export type GoalFormState = {
  status: "idle" | "success" | "error";
  message: string;
};

const goalHorizons: GoalHorizon[] = ["short_term", "long_term"];

function readHorizon(formData: FormData): GoalHorizon {
  const horizon = String(formData.get("horizon") ?? "");
  return goalHorizons.includes(horizon as GoalHorizon)
    ? (horizon as GoalHorizon)
    : "short_term";
}

export async function createGoalAction(
  _previousState: GoalFormState,
  formData: FormData,
): Promise<GoalFormState> {
  const title = String(formData.get("title") ?? "").trim();
  const description = String(formData.get("description") ?? "").trim();
  const targetDate = String(formData.get("targetDate") ?? "").trim();

  if (!title) {
    return { status: "error", message: "Add a title for your goal." };
  }

  try {
    await createGoal({
      title,
      horizon: readHorizon(formData),
      ...(description ? { description } : {}),
      ...(targetDate ? { target_date: targetDate } : {}),
    });
    revalidatePath("/");
    return { status: "success", message: "Goal added to your plan." };
  } catch {
    return {
      status: "error",
      message: "Could not save the goal. Make sure the FastAPI server is running.",
    };
  }
}

const goalStatuses: GoalStatus[] = ["active", "paused", "completed"];

export async function updateGoalStatusAction(
  _previousState: GoalFormState,
  formData: FormData,
): Promise<GoalFormState> {
  const goalId = String(formData.get("goalId") ?? "");
  const status = String(formData.get("status") ?? "") as GoalStatus;

  if (!goalId || !goalStatuses.includes(status)) {
    return { status: "error", message: "That goal update is not valid." };
  }

  try {
    await updateGoalStatus(goalId, status);
    revalidatePath("/");
    return { status: "success", message: "Goal updated." };
  } catch {
    return {
      status: "error",
      message: "Could not update the goal. Make sure FastAPI is running.",
    };
  }
}

export async function updateGoalDetailsAction(
  _previousState: GoalFormState,
  formData: FormData,
): Promise<GoalFormState> {
  const goalId = String(formData.get("goalId") ?? "");
  const title = String(formData.get("title") ?? "").trim();
  const description = String(formData.get("description") ?? "").trim();
  const targetDate = String(formData.get("targetDate") ?? "").trim();

  if (!goalId || !title) {
    return { status: "error", message: "Add a title for your goal." };
  }

  try {
    await updateGoalDetails(goalId, {
      title,
      description: description || null,
      horizon: readHorizon(formData),
      target_date: targetDate || null,
    });
    revalidatePath("/");
    return { status: "success", message: "Goal updated." };
  } catch {
    return {
      status: "error",
      message: "Could not update the goal. Make sure FastAPI is running.",
    };
  }
}

export async function archiveGoalAction(
  _previousState: GoalFormState,
  formData: FormData,
): Promise<GoalFormState> {
  const goalId = String(formData.get("goalId") ?? "");

  if (!goalId) {
    return { status: "error", message: "That goal could not be archived." };
  }

  try {
    await archiveGoal(goalId);
    revalidatePath("/");
    return { status: "success", message: "Goal archived." };
  } catch {
    return {
      status: "error",
      message: "Could not archive the goal. Make sure FastAPI is running.",
    };
  }
}

export async function restoreGoalAction(
  _previousState: GoalFormState,
  formData: FormData,
): Promise<GoalFormState> {
  const goalId = String(formData.get("goalId") ?? "");

  if (!goalId) {
    return { status: "error", message: "That goal could not be restored." };
  }

  try {
    await restoreGoal(goalId);
    revalidatePath("/");
    return { status: "success", message: "Goal restored." };
  } catch {
    return {
      status: "error",
      message: "Could not restore the goal. Make sure FastAPI is running.",
    };
  }
}

export async function deleteGoalAction(
  _previousState: GoalFormState,
  formData: FormData,
): Promise<GoalFormState> {
  const goalId = String(formData.get("goalId") ?? "");

  if (!goalId) {
    return { status: "error", message: "That goal could not be deleted." };
  }

  try {
    await deleteGoal(goalId);
    revalidatePath("/");
    return { status: "success", message: "Goal deleted." };
  } catch {
    return {
      status: "error",
      message: "Could not delete the goal. Make sure FastAPI is running.",
    };
  }
}
