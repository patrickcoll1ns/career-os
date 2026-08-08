"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { createConversation, sendMessage } from "@/lib/chat";

export type ChatFormState = {
  status: "idle" | "success" | "error";
  message: string;
};

export async function startConversationAction(): Promise<void> {
  const conversation = await createConversation();
  redirect(`/chat/${conversation.id}`);
}

export async function sendMessageAction(
  _previousState: ChatFormState,
  formData: FormData,
): Promise<ChatFormState> {
  const conversationId = String(formData.get("conversationId") ?? "");
  const content = String(formData.get("content") ?? "").trim();

  if (!conversationId || !content) {
    return { status: "error", message: "Write a message before sending." };
  }

  try {
    await sendMessage(conversationId, content);
    revalidatePath(`/chat/${conversationId}`);
    return { status: "success", message: "" };
  } catch (error) {
    return {
      status: "error",
      message:
        error instanceof Error ? error.message : "Could not send the message.",
    };
  }
}
