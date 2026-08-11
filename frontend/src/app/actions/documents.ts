"use server";

import { revalidatePath } from "next/cache";

import { DocumentUploadError, uploadDocument } from "@/lib/documents";

export type DocumentUploadState = {
  status: "idle" | "success" | "error";
  message: string;
};

const MAX_DOCUMENT_SIZE_BYTES = 5 * 1024 * 1024;
const ALLOWED_DOCUMENT_TYPES = new Set([
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
]);

export async function uploadDocumentAction(
  _previousState: DocumentUploadState,
  formData: FormData,
): Promise<DocumentUploadState> {
  const file = formData.get("file");

  if (!(file instanceof File) || file.size === 0) {
    return { status: "error", message: "Choose a PDF, DOCX, or TXT file." };
  }
  if (!ALLOWED_DOCUMENT_TYPES.has(file.type)) {
    return { status: "error", message: "Only PDF, DOCX, and TXT files are supported." };
  }
  if (file.size > MAX_DOCUMENT_SIZE_BYTES) {
    return { status: "error", message: "Documents must be 5 MB or smaller." };
  }

  try {
    const document = await uploadDocument(file);
    revalidatePath("/documents");
    if (document.status === "failed") {
      return {
        status: "error",
        message: document.error_message ?? "The document could not be processed.",
      };
    }
    return {
      status: "success",
      message: `${document.original_filename} is indexed and ready for chat.`,
    };
  } catch (error) {
    return {
      status: "error",
      message:
        error instanceof DocumentUploadError
          ? error.message
          : "Could not upload the document. Make sure FastAPI and ChromaDB are running.",
    };
  }
}
