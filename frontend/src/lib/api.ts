type HealthResponse = {
  status: "ok";
  service: string;
};

const apiUrl = process.env.API_URL ?? "http://localhost:8000";

export async function getApiHealth(): Promise<HealthResponse | null> {
  try {
    const response = await fetch(`${apiUrl}/health`, {
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
