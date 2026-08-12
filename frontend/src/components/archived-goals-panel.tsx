import { deleteGoalAction } from "@/app/actions/goals";
import { ConfirmDeleteControl } from "@/components/confirm-delete-control";
import { GoalRestoreControl } from "@/components/goal-restore-control";
import { formatDate } from "@/lib/format";
import { getArchivedGoals, type Goal } from "@/lib/goals";

function ArchivedGoalCard({ goal }: { goal: Goal }) {
  return (
    <li className="rounded-2xl border border-[#dce4dd] bg-white p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-semibold text-[#203329]">{goal.title}</h3>
          {goal.description ? (
            <p className="mt-2 text-sm leading-6 text-[#69766e]">{goal.description}</p>
          ) : null}
        </div>
        <span className="shrink-0 rounded-full bg-[#eceeec] px-2.5 py-1 text-xs font-semibold text-[#5c665f]">
          Archived
        </span>
      </div>
      <p className="mt-4 text-xs font-medium text-[#7a877f]">
        {formatDate(goal.target_date, "No target date")}
      </p>
      <GoalRestoreControl goalId={goal.id} />
      <ConfirmDeleteControl
        action={deleteGoalAction}
        idField="goalId"
        id={goal.id}
        label="goal"
      />
    </li>
  );
}

export async function ArchivedGoalsPanel() {
  const archivedGoals = await getArchivedGoals();

  if (!archivedGoals || archivedGoals.length === 0) {
    return null;
  }

  return (
    <section className="mt-10 rounded-3xl border border-[#dbe2dc] bg-[#fbfcf9] p-6 sm:p-8" aria-labelledby="archived-goals-heading">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-[#397454]">Set aside</p>
          <h2 id="archived-goals-heading" className="mt-2 text-2xl font-semibold tracking-[-0.025em]">
            Archived goals
          </h2>
        </div>
        <span className="rounded-full bg-[#eef3ed] px-3 py-1.5 text-xs font-semibold text-[#526158]">
          {archivedGoals.length} {archivedGoals.length === 1 ? "goal" : "goals"}
        </span>
      </div>

      <ul className="mt-6 space-y-3">
        {archivedGoals.map((goal) => (
          <ArchivedGoalCard key={goal.id} goal={goal} />
        ))}
      </ul>
    </section>
  );
}
