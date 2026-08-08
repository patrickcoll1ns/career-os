"use client";

import { useActionState } from "react";

import { restoreGoalAction, type GoalFormState } from "@/app/actions/goals";

const initialState: GoalFormState = { status: "idle", message: "" };

export function GoalRestoreControl({ goalId }: { goalId: string }) {
  const [state, formAction, pending] = useActionState(
    restoreGoalAction,
    initialState,
  );

  return (
    <form action={formAction} className="mt-2">
      <input type="hidden" name="goalId" value={goalId} />
      <button
        type="submit"
        disabled={pending}
        className="rounded-lg border border-[#cbd6ce] bg-white px-3 py-2 text-xs font-semibold text-[#405248] transition hover:border-[#92a99a] hover:bg-[#f6f9f6] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {pending ? "Restoring…" : "Restore"}
      </button>
      {state.status === "error" ? (
        <p className="mt-2 text-xs text-[#a14f3b]" aria-live="polite">
          {state.message}
        </p>
      ) : null}
    </form>
  );
}
