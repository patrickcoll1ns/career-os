import "server-only";

export type GoalStatus = "active" | "paused" | "completed";
export type GoalHorizon = "short_term" | "long_term";

export type Goal = {
  id: string;
  title: string;
  description: string | null;
  status: GoalStatus;
  horizon: GoalHorizon;
  target_date: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
};

export type CreateGoalInput = {
  title: string;
  description?: string;
  horizon?: GoalHorizon;
  target_date?: string;
};

const apiUrl = process.env.API_URL ?? "http://localhost:8000";

export async function getGoals(): Promise<Goal[] | null> {
  try {
    const response = await fetch(`${apiUrl}/goals`, { cache: "no-store" });

    if (!response.ok) {
      return null;
    }

    return response.json();
  } catch {
    return null;
  }
}

export async function getArchivedGoals(): Promise<Goal[] | null> {
  try {
    const response = await fetch(`${apiUrl}/goals/archived`, {
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

export async function createGoal(input: CreateGoalInput): Promise<Goal> {
  const response = await fetch(`${apiUrl}/goals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  if (!response.ok) {
    throw new Error("FastAPI could not create the goal.");
  }

  return response.json();
}

export type UpdateGoalDetailsInput = {
  title: string;
  description: string | null;
  horizon: GoalHorizon;
  target_date: string | null;
};

export async function updateGoalDetails(
  goalId: string,
  input: UpdateGoalDetailsInput,
): Promise<Goal> {
  const response = await fetch(`${apiUrl}/goals/${goalId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  if (!response.ok) {
    throw new Error("FastAPI could not update the goal.");
  }

  return response.json();
}

export async function updateGoalStatus(
  goalId: string,
  status: GoalStatus,
): Promise<Goal> {
  const response = await fetch(`${apiUrl}/goals/${goalId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });

  if (!response.ok) {
    throw new Error("FastAPI could not update the goal.");
  }

  return response.json();
}

export async function archiveGoal(goalId: string): Promise<Goal> {
  const response = await fetch(`${apiUrl}/goals/${goalId}/archive`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("FastAPI could not archive the goal.");
  }

  return response.json();
}

export async function restoreGoal(goalId: string): Promise<Goal> {
  const response = await fetch(`${apiUrl}/goals/${goalId}/restore`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("FastAPI could not restore the goal.");
  }

  return response.json();
}

export async function deleteGoal(goalId: string): Promise<void> {
  const response = await fetch(`${apiUrl}/goals/${goalId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error("FastAPI could not delete the goal.");
  }
}
