"use client";

import { useActionState, useState } from "react";

type DeleteFormState = {
  status: "idle" | "success" | "error";
  message: string;
};

type ConfirmDeleteControlProps = {
  /** Server action performing the delete. */
  action: (
    state: DeleteFormState,
    formData: FormData,
  ) => Promise<DeleteFormState>;
  /** Hidden field name the action reads the id from. */
  idField: string;
  id: string;
  /** What is being deleted, e.g. "goal" — used in the confirmation copy. */
  label: string;
  /** Overrides the confirmation sentence when archiving is not an option. */
  confirmMessage?: string;
};

const initialState: DeleteFormState = { status: "idle", message: "" };

/**
 * Two-step delete. Deletion is permanent and archiving is the recoverable
 * option, so a single stray click should never destroy an entry.
 */
export function ConfirmDeleteControl({
  action,
  idField,
  id,
  label,
  confirmMessage,
}: ConfirmDeleteControlProps) {
  const [isConfirming, setIsConfirming] = useState(false);
  const [state, formAction, pending] = useActionState(action, initialState);

  if (!isConfirming) {
    return (
      <div className="mt-2">
        <button
          type="button"
          onClick={() => setIsConfirming(true)}
          className="text-xs font-semibold text-[#7a877f] underline decoration-dotted underline-offset-2 transition hover:text-[#a14f3b]"
        >
          Delete {label}
        </button>
        {state.status === "error" ? (
          <p className="mt-2 text-xs text-[#a14f3b]" aria-live="polite">
            {state.message}
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <form action={formAction} className="mt-2">
      <input type="hidden" name={idField} value={id} />
      <p className="text-xs leading-5 text-[#805744]">
        {confirmMessage ??
          `Delete this ${label} permanently? This cannot be undone — archive it instead to keep it recoverable.`}
      </p>
      <div className="mt-2 flex flex-wrap items-center gap-3">
        <button
          type="submit"
          disabled={pending}
          className="rounded-lg bg-[#8c3f2a] px-3 py-2 text-xs font-semibold text-white transition hover:bg-[#733322] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {pending ? "Deleting…" : "Yes, delete"}
        </button>
        <button
          type="button"
          onClick={() => setIsConfirming(false)}
          className="text-xs font-semibold text-[#7a877f] transition hover:text-[#405248]"
        >
          Cancel
        </button>
      </div>
      {state.status === "error" ? (
        <p className="mt-2 text-xs text-[#a14f3b]" aria-live="polite">
          {state.message}
        </p>
      ) : null}
    </form>
  );
}
