import "server-only";

export type CareerDocument = {
  id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
  status: "pending" | "processing" | "ready" | "failed";
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

const apiUrl = process.env.API_URL ?? "http://localhost:8000";

export class DocumentUploadError extends Error {}

export async function getDocuments(): Promise<CareerDocument[] | null> {
  try {
    const response = await fetch(`${apiUrl}/documents`, { cache: "no-store" });

    if (!response.ok) {
      return null;
    }

    return response.json();
  } catch {
    return null;
  }
}

export async function uploadDocument(file: File): Promise<CareerDocument> {
  const body = new FormData();
  body.set("file", file);
  const response = await fetch(`${apiUrl}/documents`, {
    method: "POST",
    body,
  });

  if (!response.ok) {
    let message = "FastAPI could not upload the document.";
    try {
      const error = (await response.json()) as { detail?: string };
      if (error.detail) {
        message = error.detail;
      }
    } catch {}
    throw new DocumentUploadError(message);
  }

  return response.json();
}
