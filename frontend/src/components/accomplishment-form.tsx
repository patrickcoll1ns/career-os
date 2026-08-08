"use client";

import { useActionState, useEffect, useRef } from "react";

import {
  createAccomplishmentAction,
  type AccomplishmentFormState,
} from "@/app/actions/accomplishments";

const initialState: AccomplishmentFormState = { status: "idle", message: "" };

export function AccomplishmentForm() {
  const [state, formAction, pending] = useActionState(
    createAccomplishmentAction,
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
        <label className="text-sm font-medium text-[#34473c]" htmlFor="accomplishment-title">
          What did you accomplish?
        </label>
        <input
          id="accomplishment-title"
          name="title"
          type="text"
          required
          minLength={1}
          maxLength={200}
          placeholder="Shipped a feature that improved conversion by 12%"
          className="mt-2 w-full rounded-xl border border-[#ced8d0] bg-white px-4 py-3 text-sm outline-none transition placeholder:text-[#96a199] focus:border-[#4f8062] focus:ring-3 focus:ring-[#dceadf]"
        />
      </div>

      <div>
        <label className="text-sm font-medium text-[#34473c]" htmlFor="accomplishment-description">
          Details <span className="font-normal text-[#7a877f]">(optional)</span>
        </label>
        <textarea
          id="accomplishment-description"
          name="description"
          rows={3}
          placeholder="What was the impact, and what did it take to get there?"
          className="mt-2 w-full resize-none rounded-xl border border-[#ced8d0] bg-white px-4 py-3 text-sm outline-none transition placeholder:text-[#96a199] focus:border-[#4f8062] focus:ring-3 focus:ring-[#dceadf]"
        />
      </div>

      <div>
        <label className="text-sm font-medium text-[#34473c]" htmlFor="accomplishment-achieved-on">
          Date <span className="font-normal text-[#7a877f]">(optional)</span>
        </label>
        <input
          id="accomplishment-achieved-on"
          name="achievedOn"
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
          {pending ? "Adding…" : "Add accomplishment"}
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
