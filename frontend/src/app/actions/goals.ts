"use server";

import { revalidatePath } from "next/cache";

import {
  createGoal,
  type GoalStatus,
  updateGoalStatus,
} from "@/lib/goals";

export type GoalFormState = {
  status: "idle" | "success" | "error";
  message: string;
};

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
