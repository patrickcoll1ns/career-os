"use client";

import { useActionState, useState } from "react";

import {
  updateGoalDetailsAction,
  type GoalFormState,
} from "@/app/actions/goals";
import type { Goal } from "@/lib/goals";

const initialState: GoalFormState = { status: "idle", message: "" };

export function GoalEditControls({ goal }: { goal: Goal }) {
  const [isEditing, setIsEditing] = useState(false);
  const [state, formAction, pending] = useActionState(
    updateGoalDetailsAction,
    initialState,
  );
  const [handledState, setHandledState] = useState(state);

  if (state !== handledState) {
    setHandledState(state);
    if (state.status === "success") {
      setIsEditing(false);
    }
  }

  if (!isEditing) {
    return (
      <button
        type="button"
        onClick={() => setIsEditing(true)}
        className="mt-2 text-xs font-semibold text-[#405248] underline decoration-dotted underline-offset-2 transition hover:text-[#173d2c]"
      >
        Edit
      </button>
    );
  }

  return (
    <form
      action={formAction}
      className="mt-3 space-y-3 rounded-xl border border-[#e7ece8] bg-[#fbfcf9] p-4"
    >
      <input type="hidden" name="goalId" value={goal.id} />
      <div>
        <label
          className="text-xs font-medium text-[#34473c]"
          htmlFor={`edit-title-${goal.id}`}
        >
          Title
        </label>
        <input
          id={`edit-title-${goal.id}`}
          name="title"
          type="text"
          required
          minLength={1}
          maxLength={200}
          defaultValue={goal.title}
          className="mt-1 w-full rounded-lg border border-[#ced8d0] bg-white px-3 py-2 text-sm outline-none transition focus:border-[#4f8062] focus:ring-2 focus:ring-[#dceadf]"
        />
      </div>

      <div>
        <label
          className="text-xs font-medium text-[#34473c]"
          htmlFor={`edit-description-${goal.id}`}
        >
          Description
        </label>
        <textarea
          id={`edit-description-${goal.id}`}
          name="description"
          rows={2}
          defaultValue={goal.description ?? ""}
          className="mt-1 w-full resize-none rounded-lg border border-[#ced8d0] bg-white px-3 py-2 text-sm outline-none transition focus:border-[#4f8062] focus:ring-2 focus:ring-[#dceadf]"
        />
      </div>

      <div>
        <label
          className="text-xs font-medium text-[#34473c]"
          htmlFor={`edit-horizon-${goal.id}`}
        >
          Time horizon
        </label>
        <select
          id={`edit-horizon-${goal.id}`}
          name="horizon"
          defaultValue={goal.horizon}
          className="mt-1 w-full rounded-lg border border-[#ced8d0] bg-white px-3 py-2 text-sm outline-none transition focus:border-[#4f8062] focus:ring-2 focus:ring-[#dceadf]"
        >
          <option value="short_term">Short term</option>
          <option value="long_term">Long term</option>
        </select>
      </div>

      <div>
        <label
          className="text-xs font-medium text-[#34473c]"
          htmlFor={`edit-target-date-${goal.id}`}
        >
          Target date
        </label>
        <input
          id={`edit-target-date-${goal.id}`}
          name="targetDate"
          type="date"
          defaultValue={goal.target_date ?? ""}
          className="mt-1 w-full rounded-lg border border-[#ced8d0] bg-white px-3 py-2 text-sm outline-none transition focus:border-[#4f8062] focus:ring-2 focus:ring-[#dceadf]"
        />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="submit"
          disabled={pending}
          className="rounded-lg bg-[#173d2c] px-3 py-2 text-xs font-semibold text-white transition hover:bg-[#24543d] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {pending ? "Saving…" : "Save"}
        </button>
        <button
          type="button"
          onClick={() => setIsEditing(false)}
          className="text-xs font-semibold text-[#7a877f] transition hover:text-[#405248]"
        >
          Cancel
        </button>
      </div>
      {state.status === "error" ? (
        <p className="text-xs text-[#a14f3b]" aria-live="polite">
          {state.message}
        </p>
      ) : null}
    </form>
  );
}
