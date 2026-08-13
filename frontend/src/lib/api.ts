type HealthResponse = {
  status: "ok";
  service: string;
};

export async function getApiHealth(): Promise<HealthResponse | null> {
  try {
    const response = await backendFetch("/health", {
      cache: "no-store",
      signal: AbortSignal.timeout(1500),
    });

    if (!response.ok) {
      return null;
    }

    const health: HealthResponse = await response.json();
    return health.status === "ok" ? health : null;
  } catch {
    return null;
  }
}
import { backendFetch } from "@/lib/backend-api";
