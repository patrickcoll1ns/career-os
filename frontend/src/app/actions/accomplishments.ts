"use server";

import { revalidatePath } from "next/cache";

import { createAccomplishment } from "@/lib/accomplishments";

export type AccomplishmentFormState = {
  status: "idle" | "success" | "error";
  message: string;
};

export async function createAccomplishmentAction(
  _previousState: AccomplishmentFormState,
  formData: FormData,
): Promise<AccomplishmentFormState> {
  const title = String(formData.get("title") ?? "").trim();
  const description = String(formData.get("description") ?? "").trim();
  const achievedOn = String(formData.get("achievedOn") ?? "").trim();

  if (!title) {
    return { status: "error", message: "Add a title for your accomplishment." };
  }

  try {
    await createAccomplishment({
      title,
      ...(description ? { description } : {}),
      ...(achievedOn ? { achieved_on: achievedOn } : {}),
    });
    revalidatePath("/");
    return { status: "success", message: "Accomplishment added." };
  } catch {
    return {
      status: "error",
      message: "Could not save the accomplishment. Make sure the FastAPI server is running.",
    };
  }
}
