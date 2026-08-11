import "server-only";

export type MessageRole = "user" | "assistant";

export type MessageSource = {
  document_id: string;
  filename: string;
  chunk_index: number;
};

export type Message = {
  id: string;
  role: MessageRole;
  content: string;
  sources: MessageSource[];
  created_at: string;
};

export type Conversation = {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
};

export type ConversationWithMessages = Conversation & {
  messages: Message[];
};

const apiUrl = process.env.API_URL ?? "http://localhost:8000";

export async function getConversations(): Promise<Conversation[] | null> {
  try {
    const response = await fetch(`${apiUrl}/chat/conversations`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return response.json();
  } catch {
    return null;
  }
}

export async function getConversation(
  conversationId: string,
): Promise<ConversationWithMessages | null> {
  try {
    const response = await fetch(
      `${apiUrl}/chat/conversations/${conversationId}`,
      { cache: "no-store" },
    );

    if (!response.ok) {
      return null;
    }

    return response.json();
  } catch {
    return null;
  }
}

export async function createConversation(): Promise<Conversation> {
  const response = await fetch(`${apiUrl}/chat/conversations`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("FastAPI could not start a conversation.");
  }

  return response.json();
}

export async function sendMessage(
  conversationId: string,
  content: string,
): Promise<ConversationWithMessages> {
  const response = await fetch(
    `${apiUrl}/chat/conversations/${conversationId}/messages`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    },
  );

  if (!response.ok) {
    if (response.status === 502) {
      throw new Error(
        "The career copilot is unavailable right now. Make sure ANTHROPIC_API_KEY is set on the backend.",
      );
    }
    throw new Error("FastAPI could not send the message.");
  }

  return response.json();
}
