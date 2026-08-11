"use client";

import { useActionState } from "react";

import {
  startInterviewAction,
  type InterviewSetupFormState,
} from "@/app/actions/interviews";

const initialState: InterviewSetupFormState = { status: "idle", message: "" };

export function InterviewSetupForm() {
  const [state, formAction, pending] = useActionState(
    startInterviewAction,
    initialState,
  );

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <label className="text-sm font-medium text-[#34473c]" htmlFor="target-role">
          Target role
        </label>
        <input
          id="target-role"
          name="targetRole"
          type="text"
          required
          maxLength={200}
          placeholder="Backend engineering intern"
          className="mt-2 w-full rounded-xl border border-[#ced8d0] bg-white px-4 py-3 text-sm outline-none transition placeholder:text-[#96a199] focus:border-[#4f8062] focus:ring-3 focus:ring-[#dceadf]"
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="text-sm font-medium text-[#34473c]" htmlFor="interview-type">
            Interview type
          </label>
          <select
            id="interview-type"
            name="interviewType"
            required
            defaultValue="behavioral"
            className="mt-2 w-full rounded-xl border border-[#ced8d0] bg-white px-4 py-3 text-sm outline-none transition focus:border-[#4f8062] focus:ring-3 focus:ring-[#dceadf]"
          >
            <option value="behavioral">Behavioral</option>
            <option value="technical">Technical</option>
            <option value="mixed">Mixed</option>
          </select>
        </div>

        <div>
          <label className="text-sm font-medium text-[#34473c]" htmlFor="difficulty">
            Difficulty
          </label>
          <select
            id="difficulty"
            name="difficulty"
            required
            defaultValue="intermediate"
            className="mt-2 w-full rounded-xl border border-[#ced8d0] bg-white px-4 py-3 text-sm outline-none transition focus:border-[#4f8062] focus:ring-3 focus:ring-[#dceadf]"
          >
            <option value="introductory">Introductory</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>
      </div>

      <div>
        <label className="text-sm font-medium text-[#34473c]" htmlFor="question-limit">
          Number of questions
        </label>
        <input
          id="question-limit"
          name="questionLimit"
          type="number"
          min={1}
          max={20}
          required
          defaultValue={5}
          className="mt-2 w-full rounded-xl border border-[#ced8d0] bg-white px-4 py-3 text-sm outline-none transition focus:border-[#4f8062] focus:ring-3 focus:ring-[#dceadf]"
        />
      </div>

      <div className="rounded-xl border border-[#d8ded8] bg-[#f4f7f2] p-3 text-xs leading-5 text-[#65736b]">
        Claude asks one question at a time, scores each answer, and gives a final
        debrief once you finish the session.
      </div>

      <button
        type="submit"
        disabled={pending}
        className="rounded-xl bg-[#173d2c] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#24543d] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {pending ? "Starting interview…" : "Start interview"}
      </button>
      <p className="text-sm text-[#a14f3b]" aria-live="polite">
        {state.message}
      </p>
    </form>
  );
}
