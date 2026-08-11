import Link from "next/link";

import { ChatMessageForm } from "@/components/chat-message-form";
import { MarkdownMessage } from "@/components/markdown-message";
import { formatTimestamp } from "@/lib/format";
import { getConversation, type Message } from "@/lib/chat";

const roleStyles: Record<Message["role"], string> = {
  user: "ml-auto bg-[#173d2c] text-white",
  assistant: "mr-auto bg-white text-[#203329] border border-[#dce4dd]",
};

function MessageBubble({ message }: { message: Message }) {
  return (
    <li className={`max-w-[85%] rounded-2xl px-4 py-3 ${roleStyles[message.role]}`}>
      {message.role === "assistant" ? (
        <>
          <MarkdownMessage content={message.content} />
          {message.sources.length > 0 ? (
            <div className="mt-4 border-t border-[#e2e8e3] pt-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#6d7b73]">
                Sources
              </p>
              <ul className="mt-2 flex flex-wrap gap-2">
                {message.sources.map((source) => (
                  <li
                    key={`${source.document_id}:${source.chunk_index}`}
                    className="rounded-full bg-[#edf3ee] px-2.5 py-1 text-xs font-medium text-[#397454]"
                  >
                    {source.filename} · section {source.chunk_index + 1}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </>
      ) : (
        <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
      )}
      <p
        className={`mt-2 text-[11px] font-medium ${
          message.role === "user" ? "text-[#c9d6cd]" : "text-[#8a9690]"
        }`}
      >
        {formatTimestamp(message.created_at)}
      </p>
    </li>
  );
}

export default async function ChatConversationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const conversation = await getConversation(id);

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
            href="/chat"
            className="text-sm font-semibold text-[#397454] hover:text-[#173d2c]"
          >
            All conversations
          </Link>
        </div>
      </header>

      <div className="mx-auto max-w-3xl px-6 py-12">
        {conversation === null ? (
          <div className="rounded-2xl border border-[#e1c9be] bg-[#fff8f4] p-5 text-sm leading-6 text-[#805744]">
            This conversation is unavailable. Make sure FastAPI is running on port
            8000, then refresh this page.
          </div>
        ) : (
          <>
            <p className="text-sm font-medium text-[#397454]">Career copilot</p>
            <h1 className="mt-2 text-2xl font-semibold tracking-[-0.02em]">
              {conversation.title ?? "Untitled conversation"}
            </h1>

            <div className="mt-8 rounded-3xl border border-[#dbe2dc] bg-[#eef3ed] p-6 sm:p-8">
              {conversation.messages.length === 0 ? (
                <p className="text-sm leading-6 text-[#69766e]">
                  Send a message to start the conversation. Your reply will be
                  grounded in your current goals, accomplishments, and relevant
                  uploaded documents.
                </p>
              ) : (
                <ul className="flex flex-col gap-3">
                  {conversation.messages.map((message) => (
                    <MessageBubble key={message.id} message={message} />
                  ))}
                </ul>
              )}

              <ChatMessageForm conversationId={conversation.id} />
            </div>
          </>
        )}
      </div>
    </main>
  );
}
