"use client";

import { useActionState } from "react";

import { archiveGoalAction, type GoalFormState } from "@/app/actions/goals";

const initialState: GoalFormState = { status: "idle", message: "" };

export function GoalArchiveControl({ goalId }: { goalId: string }) {
  const [state, formAction, pending] = useActionState(
    archiveGoalAction,
    initialState,
  );

  return (
    <form action={formAction} className="mt-2">
      <input type="hidden" name="goalId" value={goalId} />
      <button
        type="submit"
        disabled={pending}
        className="text-xs font-semibold text-[#7a877f] underline decoration-dotted underline-offset-2 transition hover:text-[#a14f3b] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {pending ? "Archiving…" : "Archive goal"}
      </button>
      {state.status === "error" ? (
        <p className="mt-2 text-xs text-[#a14f3b]" aria-live="polite">
          {state.message}
        </p>
      ) : null}
    </form>
  );
}
