"use client";

import { useActionState } from "react";

import {
  archiveAccomplishmentAction,
  restoreAccomplishmentAction,
  type AccomplishmentFormState,
} from "@/app/actions/accomplishments";

const initialState: AccomplishmentFormState = { status: "idle", message: "" };

type AccomplishmentArchiveControlProps = {
  accomplishmentId: string;
  /** "archive" moves an entry out of the journal; "restore" brings it back. */
  mode: "archive" | "restore";
};

export function AccomplishmentArchiveControl({
  accomplishmentId,
  mode,
}: AccomplishmentArchiveControlProps) {
  const isArchiving = mode === "archive";
  const [state, formAction, pending] = useActionState(
    isArchiving ? archiveAccomplishmentAction : restoreAccomplishmentAction,
    initialState,
  );

  const idleLabel = isArchiving ? "Archive" : "Restore";
  const pendingLabel = isArchiving ? "Archiving…" : "Restoring…";

  return (
    <form action={formAction} className="mt-2">
      <input type="hidden" name="accomplishmentId" value={accomplishmentId} />
      <button
        type="submit"
        disabled={pending}
        className="text-xs font-semibold text-[#7a877f] underline decoration-dotted underline-offset-2 transition hover:text-[#405248] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {pending ? pendingLabel : idleLabel}
      </button>
      {state.status === "error" ? (
        <p className="mt-2 text-xs text-[#a14f3b]" aria-live="polite">
          {state.message}
        </p>
      ) : null}
    </form>
  );
}
