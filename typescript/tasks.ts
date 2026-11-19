export type TaskStatus = "pending" | "in_progress" | "completed";

export interface Task {
  id: string;
  companyId: string;
  assignedTo: string;
  title: string;
  description: string;
  status: TaskStatus;
  dueDate?: string;
}

export class TaskApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "TaskApiError";
  }
}

export function filterTasksByStatus(tasks: readonly Task[], status: TaskStatus): Task[] {
  return tasks.filter((task) => task.status === status);
}

export function calculateCompletionPercentage(tasks: readonly Task[]): number {
  if (tasks.length === 0) return 0;
  const completed = filterTasksByStatus(tasks, "completed").length;
  return Math.round((completed / tasks.length) * 100);
}

export async function fetchTasks(apiBaseUrl: string, accessToken: string): Promise<Task[]> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/tasks`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  } catch {
    throw new TaskApiError("Unable to reach the task API", 0);
  }

  if (!response.ok) {
    throw new TaskApiError("Unable to fetch tasks", response.status);
  }
  const data: unknown = await response.json();
  if (!Array.isArray(data)) throw new TaskApiError("Task API returned an invalid response", 502);
  return data as Task[];
}
