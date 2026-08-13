import "server-only";

import { createHmac } from "node:crypto";

import { auth } from "@/auth";

const apiUrl = process.env.API_URL ?? "http://localhost:8000";

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
  const payload = `${method}\n${url.pathname}${url.search}\n${timestamp}\n${ownerId}`;
  const signature = createHmac("sha256", secret).update(payload).digest("hex");
  const headers = new Headers(init.headers);
  headers.set("X-CareerOS-User", ownerId);
  headers.set("X-CareerOS-Timestamp", timestamp);
  headers.set("X-CareerOS-Signature", signature);

  return fetch(url, { ...init, headers });
}
