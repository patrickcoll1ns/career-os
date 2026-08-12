"use server";

import { revalidatePath } from "next/cache";

import {
  archiveAccomplishment,
  createAccomplishment,
  deleteAccomplishment,
  restoreAccomplishment,
} from "@/lib/accomplishments";

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

async function runAccomplishmentAction(
  formData: FormData,
  action: (accomplishmentId: string) => Promise<unknown>,
  { successMessage, failureMessage }: Record<"successMessage" | "failureMessage", string>,
): Promise<AccomplishmentFormState> {
  const accomplishmentId = String(formData.get("accomplishmentId") ?? "");

  if (!accomplishmentId) {
    return { status: "error", message: failureMessage };
  }

  try {
    await action(accomplishmentId);
    revalidatePath("/");
    return { status: "success", message: successMessage };
  } catch {
    return {
      status: "error",
      message: `${failureMessage} Make sure FastAPI is running.`,
    };
  }
}

export async function archiveAccomplishmentAction(
  _previousState: AccomplishmentFormState,
  formData: FormData,
): Promise<AccomplishmentFormState> {
  return runAccomplishmentAction(formData, archiveAccomplishment, {
    successMessage: "Accomplishment archived.",
    failureMessage: "Could not archive the accomplishment.",
  });
}

export async function restoreAccomplishmentAction(
  _previousState: AccomplishmentFormState,
  formData: FormData,
): Promise<AccomplishmentFormState> {
  return runAccomplishmentAction(formData, restoreAccomplishment, {
    successMessage: "Accomplishment restored.",
    failureMessage: "Could not restore the accomplishment.",
  });
}

export async function deleteAccomplishmentAction(
  _previousState: AccomplishmentFormState,
  formData: FormData,
): Promise<AccomplishmentFormState> {
  return runAccomplishmentAction(formData, deleteAccomplishment, {
    successMessage: "Accomplishment deleted.",
    failureMessage: "Could not delete the accomplishment.",
  });
}
