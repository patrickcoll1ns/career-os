"use client";

import { useActionState, useEffect, useRef } from "react";

import {
  type DocumentUploadState,
  uploadDocumentAction,
} from "@/app/actions/documents";

const initialState: DocumentUploadState = { status: "idle", message: "" };

export function DocumentUploadForm() {
  const [state, formAction, pending] = useActionState(
    uploadDocumentAction,
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
        <label className="text-sm font-medium text-[#34473c]" htmlFor="career-document">
          Choose a career document
        </label>
        <input
          id="career-document"
          name="file"
          type="file"
          accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
          required
          className="mt-2 block w-full rounded-xl border border-[#ced8d0] bg-white px-4 py-3 text-sm text-[#526158] file:mr-4 file:rounded-lg file:border-0 file:bg-[#e3ede5] file:px-3 file:py-2 file:text-sm file:font-semibold file:text-[#315f44] hover:file:bg-[#d6e6d9]"
        />
        <p className="mt-2 text-xs leading-5 text-[#7a877f]">
          PDF, DOCX, or TXT · maximum 5 MB. Relevant excerpts may be sent to Claude
          when they help answer a chat question.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="submit"
          disabled={pending}
          className="rounded-xl bg-[#173d2c] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#24543d] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {pending ? "Extracting and indexing…" : "Upload document"}
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
