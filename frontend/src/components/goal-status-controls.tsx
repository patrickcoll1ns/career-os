"use client";

import { useActionState } from "react";

import {
  updateGoalStatusAction,
  type GoalFormState,
} from "@/app/actions/goals";
import type { GoalStatus } from "@/lib/goals";

const initialState: GoalFormState = { status: "idle", message: "" };

type StatusOption = {
  label: string;
  value: GoalStatus;
  primary?: boolean;
};

const optionsByStatus: Record<GoalStatus, StatusOption[]> = {
  active: [
    { label: "Pause", value: "paused" },
    { label: "Mark complete", value: "completed", primary: true },
  ],
  paused: [
    { label: "Resume", value: "active" },
    { label: "Mark complete", value: "completed", primary: true },
  ],
  completed: [{ label: "Reopen", value: "active" }],
};

export function GoalStatusControls({
  goalId,
  status,
}: {
  goalId: string;
  status: GoalStatus;
}) {
  const [state, formAction, pending] = useActionState(
    updateGoalStatusAction,
    initialState,
  );

  return (
    <div className="mt-4 border-t border-[#e7ece8] pt-4">
      <form action={formAction} className="flex flex-wrap gap-2">
        <input type="hidden" name="goalId" value={goalId} />
        {optionsByStatus[status].map((option) => (
          <button
            key={option.value}
            type="submit"
            name="status"
            value={option.value}
            disabled={pending}
            className={
              option.primary
                ? "rounded-lg bg-[#173d2c] px-3 py-2 text-xs font-semibold text-white transition hover:bg-[#24543d] disabled:cursor-not-allowed disabled:opacity-60"
                : "rounded-lg border border-[#cbd6ce] bg-white px-3 py-2 text-xs font-semibold text-[#405248] transition hover:border-[#92a99a] hover:bg-[#f6f9f6] disabled:cursor-not-allowed disabled:opacity-60"
            }
          >
            {pending ? "Updating…" : option.label}
          </button>
        ))}
      </form>
      {state.status === "error" ? (
        <p className="mt-2 text-xs text-[#a14f3b]" aria-live="polite">
          {state.message}
        </p>
      ) : null}
    </div>
  );
}
