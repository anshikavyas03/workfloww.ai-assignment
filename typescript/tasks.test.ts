import assert from "node:assert/strict";
import test from "node:test";
import { calculateCompletionPercentage, filterTasksByStatus, type Task } from "./tasks.js";

const tasks: Task[] = [
  { id: "1", companyId: "c1", assignedTo: "u1", title: "First", description: "", status: "completed" },
  { id: "2", companyId: "c1", assignedTo: "u2", title: "Second", description: "", status: "pending" },
];

test("filters tasks by status", () => {
  assert.deepEqual(filterTasksByStatus(tasks, "pending").map((task) => task.id), ["2"]);
});

test("calculates completion percentage and handles an empty list", () => {
  assert.equal(calculateCompletionPercentage(tasks), 50);
  assert.equal(calculateCompletionPercentage([]), 0);
});
