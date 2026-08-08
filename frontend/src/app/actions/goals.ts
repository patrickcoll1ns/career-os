"use server";

import { revalidatePath } from "next/cache";

import { createGoal } from "@/lib/goals";

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
