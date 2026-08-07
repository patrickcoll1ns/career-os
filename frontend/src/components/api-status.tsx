import { connection } from "next/server";

import { getApiHealth } from "@/lib/api";

export function ApiStatusFallback() {
  return (
    <span className="flex items-center gap-2 text-xs font-medium text-[#6f7b74]">
      <span className="size-2 rounded-full bg-[#c4cbc6]" />
      Checking API
    </span>
  );
}

export async function ApiStatus() {
  await connection();
  const health = await getApiHealth();
  const online = health?.status === "ok";

  return (
    <span
      className={`flex items-center gap-2 text-xs font-medium ${
        online ? "text-[#397454]" : "text-[#8a5a45]"
      }`}
      role="status"
    >
      <span
        className={`size-2 rounded-full ${online ? "bg-[#66a97d]" : "bg-[#c98a6b]"}`}
        aria-hidden="true"
      />
      {online ? "API connected" : "API offline"}
    </span>
  );
}
