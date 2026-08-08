import Link from "next/link";

import { startConversationAction } from "@/app/actions/chat";
import { formatTimestamp } from "@/lib/format";
import { getConversations } from "@/lib/chat";

export default async function ChatPage() {
  const conversations = await getConversations();

  return (
    <main className="min-h-screen bg-[#f5f7f2] text-[#16251d]">
      <header className="border-b border-[#dfe5dc] bg-[#fbfcf8]/90">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-5">
          <Link className="flex items-center gap-3" href="/">
            <span className="grid size-10 place-items-center rounded-xl bg-[#173d2c] text-sm font-bold text-white">
              CO
            </span>
            <span>
              <span className="block text-lg font-semibold leading-none">CareerOS</span>
              <span className="mt-1 block text-xs text-[#617068]">Career copilot</span>
            </span>
          </Link>
          <Link
            href="/"
            className="text-sm font-semibold text-[#397454] hover:text-[#173d2c]"
          >
            Back to dashboard
          </Link>
        </div>
      </header>

      <div className="mx-auto max-w-3xl px-6 py-12">
        <p className="text-sm font-medium text-[#397454]">Career copilot</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-[-0.02em]">
          Your conversations
        </h1>
        <p className="mt-3 text-sm leading-6 text-[#69766e]">
          Get coaching grounded in your current goals and accomplishments.
        </p>

        <form action={startConversationAction} className="mt-7">
          <button
            type="submit"
            className="rounded-xl bg-[#173d2c] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#24543d]"
          >
            Start a new conversation
          </button>
        </form>

        <div className="mt-10">
          {conversations === null ? (
            <div className="rounded-2xl border border-[#e1c9be] bg-[#fff8f4] p-5 text-sm leading-6 text-[#805744]">
              Conversations are unavailable. Start FastAPI on port 8000, then refresh this page.
            </div>
          ) : conversations.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-[#c9d5cc] bg-white/70 p-8 text-center">
              <p className="font-medium text-[#405248]">No conversations yet</p>
              <p className="mt-2 text-sm text-[#748078]">
                Start one above to talk through your next career move.
              </p>
            </div>
          ) : (
            <ul className="space-y-3">
              {conversations.map((conversation) => (
                <li key={conversation.id}>
                  <Link
                    href={`/chat/${conversation.id}`}
                    className="block rounded-2xl border border-[#dce4dd] bg-white p-5 transition hover:border-[#92a99a]"
                  >
                    <p className="font-semibold text-[#203329]">
                      {conversation.title ?? "Untitled conversation"}
                    </p>
                    <p className="mt-2 text-xs font-medium text-[#7a877f]">
                      {formatTimestamp(conversation.updated_at)}
                    </p>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </main>
  );
}
