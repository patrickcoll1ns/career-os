import "server-only";

export type Accomplishment = {
  id: string;
  title: string;
  description: string | null;
  achieved_on: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
};

export type CreateAccomplishmentInput = {
  title: string;
  description?: string;
  achieved_on?: string;
};

const apiUrl = process.env.API_URL ?? "http://localhost:8000";

export async function getAccomplishments(): Promise<Accomplishment[] | null> {
  try {
    const response = await fetch(`${apiUrl}/accomplishments`, {
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

export async function getArchivedAccomplishments(): Promise<
  Accomplishment[] | null
> {
  try {
    const response = await fetch(`${apiUrl}/accomplishments/archived`, {
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

export async function createAccomplishment(
  input: CreateAccomplishmentInput,
): Promise<Accomplishment> {
  const response = await fetch(`${apiUrl}/accomplishments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  if (!response.ok) {
    throw new Error("FastAPI could not create the accomplishment.");
  }

  return response.json();
}

export async function archiveAccomplishment(
  accomplishmentId: string,
): Promise<Accomplishment> {
  const response = await fetch(
    `${apiUrl}/accomplishments/${accomplishmentId}/archive`,
    { method: "POST" },
  );

  if (!response.ok) {
    throw new Error("FastAPI could not archive the accomplishment.");
  }

  return response.json();
}

export async function restoreAccomplishment(
  accomplishmentId: string,
): Promise<Accomplishment> {
  const response = await fetch(
    `${apiUrl}/accomplishments/${accomplishmentId}/restore`,
    { method: "POST" },
  );

  if (!response.ok) {
    throw new Error("FastAPI could not restore the accomplishment.");
  }

  return response.json();
}

export async function deleteAccomplishment(
  accomplishmentId: string,
): Promise<void> {
  const response = await fetch(`${apiUrl}/accomplishments/${accomplishmentId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error("FastAPI could not delete the accomplishment.");
  }
}
