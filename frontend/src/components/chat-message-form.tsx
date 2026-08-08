"use client";

import { useActionState, useEffect, useRef } from "react";

import { sendMessageAction, type ChatFormState } from "@/app/actions/chat";

const initialState: ChatFormState = { status: "idle", message: "" };

export function ChatMessageForm({ conversationId }: { conversationId: string }) {
  const [state, formAction, pending] = useActionState(
    sendMessageAction,
    initialState,
  );
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (state.status === "success") {
      formRef.current?.reset();
    }
  }, [state.status]);

  return (
    <form ref={formRef} action={formAction} className="mt-6">
      <input type="hidden" name="conversationId" value={conversationId} />
      <label className="text-sm font-medium text-[#34473c]" htmlFor="chat-content">
        Your message
      </label>
      <textarea
        id="chat-content"
        name="content"
        rows={3}
        required
        maxLength={8000}
        placeholder="Ask about your next career move..."
        className="mt-2 w-full resize-none rounded-xl border border-[#ced8d0] bg-white px-4 py-3 text-sm outline-none transition placeholder:text-[#96a199] focus:border-[#4f8062] focus:ring-3 focus:ring-[#dceadf]"
      />
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <button
          type="submit"
          disabled={pending}
          className="rounded-xl bg-[#173d2c] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#24543d] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {pending ? "Sending…" : "Send"}
        </button>
        {state.status === "error" ? (
          <p className="text-sm text-[#a14f3b]" aria-live="polite">
            {state.message}
          </p>
        ) : null}
      </div>
    </form>
  );
}
