import "server-only";

import { createHash, createHmac } from "node:crypto";

import { auth } from "@/auth";

const apiUrl = process.env.API_URL ?? "http://localhost:8000";
const EMPTY_BODY_SHA256 = createHash("sha256").update("").digest("hex");

/**
 * Hash the exact bytes FastAPI will receive.
 *
 * Multipart uploads are streamed and are never buffered on either side, so they
 * sign the empty digest; the backend skips the body comparison for them and
 * relies on its own size and content validation instead.
 */
function bodyDigest(body: BodyInit | null | undefined): string {
  if (body === null || body === undefined) {
    return EMPTY_BODY_SHA256;
  }
  if (typeof body === "string") {
    return createHash("sha256").update(body, "utf8").digest("hex");
  }
  if (body instanceof Uint8Array) {
    return createHash("sha256").update(body).digest("hex");
  }
  if (body instanceof ArrayBuffer) {
    return createHash("sha256").update(Buffer.from(body)).digest("hex");
  }
  return EMPTY_BODY_SHA256;
}

export async function backendFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const session = await auth();
  const ownerId = session?.user?.ownerId;
  const secret = process.env.INTERNAL_AUTH_SECRET;
  if (!ownerId || !secret) {
    throw new Error("CareerOS authentication is not configured.");
  }

  const url = new URL(path, apiUrl);
  if (url.origin !== new URL(apiUrl).origin) {
    throw new Error("Refusing to call an untrusted backend origin.");
  }

  const timestamp = Math.floor(Date.now() / 1000).toString();
  const method = (init.method ?? "GET").toUpperCase();
  const digest = bodyDigest(init.body);
  const payload = [
    method,
    `${url.pathname}${url.search}`,
    timestamp,
    ownerId,
    digest,
  ].join("\n");
  const signature = createHmac("sha256", secret).update(payload).digest("hex");
  const headers = new Headers(init.headers);
  headers.set("X-CareerOS-User", ownerId);
  headers.set("X-CareerOS-Timestamp", timestamp);
  headers.set("X-CareerOS-Signature", signature);
  headers.set("X-CareerOS-Content-SHA256", digest);

  return fetch(url, { ...init, headers });
}
