"use client";

import { useActionState } from "react";

import {
  createResumeReviewAction,
  type ResumeReviewFormState,
} from "@/app/actions/resume-reviews";

type ReviewableDocument = {
  id: string;
  original_filename: string;
};

const initialState: ResumeReviewFormState = { status: "idle", message: "" };

export function ResumeReviewForm({ documents }: { documents: ReviewableDocument[] }) {
  const [state, formAction, pending] = useActionState(
    createResumeReviewAction,
    initialState,
  );

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <label className="text-sm font-medium text-[#34473c]" htmlFor="review-document">
          Indexed resume
        </label>
        <select
          id="review-document"
          name="documentId"
          required
          defaultValue=""
          className="mt-2 w-full rounded-xl border border-[#ced8d0] bg-white px-4 py-3 text-sm outline-none transition focus:border-[#4f8062] focus:ring-3 focus:ring-[#dceadf]"
        >
          <option value="" disabled>
            Select a document
          </option>
          {documents.map((document) => (
            <option key={document.id} value={document.id}>
              {document.original_filename}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="text-sm font-medium text-[#34473c]" htmlFor="target-role">
          Target role <span className="font-normal text-[#7a877f]">(optional)</span>
        </label>
        <input
          id="target-role"
          name="targetRole"
          type="text"
          maxLength={200}
          placeholder="Backend engineering intern"
          className="mt-2 w-full rounded-xl border border-[#ced8d0] bg-white px-4 py-3 text-sm outline-none transition placeholder:text-[#96a199] focus:border-[#4f8062] focus:ring-3 focus:ring-[#dceadf]"
        />
      </div>

      <div className="rounded-xl border border-[#d8ded8] bg-[#f4f7f2] p-3 text-xs leading-5 text-[#65736b]">
        Generating a review sends the selected document&apos;s full extracted text to
        Anthropic. Claude is instructed to treat it as untrusted content and avoid
        inventing experience or metrics.
      </div>

      <button
        type="submit"
        disabled={pending || documents.length === 0}
        className="rounded-xl bg-[#173d2c] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#24543d] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {pending ? "Reviewing resume…" : "Generate review"}
      </button>
      <p className="text-sm text-[#a14f3b]" aria-live="polite">
        {state.message}
      </p>
    </form>
  );
}
