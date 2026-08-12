"use client";

import { useActionState, useEffect, useRef } from "react";

import { createGoalAction, type GoalFormState } from "@/app/actions/goals";

const initialState: GoalFormState = { status: "idle", message: "" };

export function GoalForm() {
  const [state, formAction, pending] = useActionState(
    createGoalAction,
    initialState,
  );
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (state.status === "success") {
      formRef.current?.reset();
    }
  }, [state.status]);

  return (
    <form ref={formRef} action={formAction} className="space-y-4">
      <div>
        <label className="text-sm font-medium text-[#34473c]" htmlFor="goal-title">
          Goal title
        </label>
        <input
          id="goal-title"
          name="title"
          type="text"
          required
          minLength={1}
          maxLength={200}
          placeholder="Land a backend engineering role"
          className="mt-2 w-full rounded-xl border border-[#ced8d0] bg-white px-4 py-3 text-sm outline-none transition placeholder:text-[#96a199] focus:border-[#4f8062] focus:ring-3 focus:ring-[#dceadf]"
        />
      </div>

      <div>
        <label className="text-sm font-medium text-[#34473c]" htmlFor="goal-description">
          Why it matters <span className="font-normal text-[#7a877f]">(optional)</span>
        </label>
        <textarea
          id="goal-description"
          name="description"
          rows={3}
          placeholder="Build experience and confidence through focused projects."
          className="mt-2 w-full resize-none rounded-xl border border-[#ced8d0] bg-white px-4 py-3 text-sm outline-none transition placeholder:text-[#96a199] focus:border-[#4f8062] focus:ring-3 focus:ring-[#dceadf]"
        />
      </div>

      <div>
        <label className="text-sm font-medium text-[#34473c]" htmlFor="goal-horizon">
          Time horizon
        </label>
        <select
          id="goal-horizon"
          name="horizon"
          defaultValue="short_term"
          className="mt-2 w-full rounded-xl border border-[#ced8d0] bg-white px-4 py-3 text-sm outline-none transition focus:border-[#4f8062] focus:ring-3 focus:ring-[#dceadf]"
        >
          <option value="short_term">Short term</option>
          <option value="long_term">Long term</option>
        </select>
      </div>

      <div>
        <label className="text-sm font-medium text-[#34473c]" htmlFor="goal-target-date">
          Target date <span className="font-normal text-[#7a877f]">(optional)</span>
        </label>
        <input
          id="goal-target-date"
          name="targetDate"
          type="date"
          className="mt-2 w-full rounded-xl border border-[#ced8d0] bg-white px-4 py-3 text-sm outline-none transition focus:border-[#4f8062] focus:ring-3 focus:ring-[#dceadf]"
        />
      </div>

      <div className="flex flex-wrap items-center gap-3 pt-1">
        <button
          type="submit"
          disabled={pending}
          className="rounded-xl bg-[#173d2c] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#24543d] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {pending ? "Adding goal…" : "Add goal"}
        </button>
        <p
          className={`text-sm ${
            state.status === "error" ? "text-[#a14f3b]" : "text-[#397454]"
          }`}
          aria-live="polite"
        >
          {state.message}
        </p>
      </div>
    </form>
  );
}
