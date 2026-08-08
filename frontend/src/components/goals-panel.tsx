import { GoalForm } from "@/components/goal-form";
import { getGoals, type Goal } from "@/lib/goals";

function formatTargetDate(value: string | null) {
  if (!value) return "No target date";

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}

function GoalCard({ goal }: { goal: Goal }) {
  return (
    <li className="rounded-2xl border border-[#dce4dd] bg-white p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-semibold text-[#203329]">{goal.title}</h3>
          {goal.description ? (
            <p className="mt-2 text-sm leading-6 text-[#69766e]">{goal.description}</p>
          ) : null}
        </div>
        <span className="shrink-0 rounded-full bg-[#e4efe7] px-2.5 py-1 text-xs font-semibold capitalize text-[#397454]">
          {goal.status}
        </span>
      </div>
      <p className="mt-4 text-xs font-medium text-[#7a877f]">
        {formatTargetDate(goal.target_date)}
      </p>
    </li>
  );
}

export async function GoalsPanel() {
  const goals = await getGoals();

  return (
    <section className="mt-16 grid gap-6 lg:grid-cols-[0.85fr_1.15fr]" aria-labelledby="goals-heading">
      <div className="rounded-3xl border border-[#dbe2dc] bg-[#fbfcf9] p-6 sm:p-8">
        <p className="text-sm font-medium text-[#397454]">Add direction</p>
        <h2 id="goals-heading" className="mt-2 text-2xl font-semibold tracking-[-0.025em]">
          Create a career goal
        </h2>
        <p className="mt-3 text-sm leading-6 text-[#69766e]">
          Capture an outcome you want to work toward. You can refine the plan as CareerOS grows.
        </p>
        <div className="mt-7">
          <GoalForm />
        </div>
      </div>

      <div className="rounded-3xl border border-[#dbe2dc] bg-[#eef3ed] p-6 sm:p-8">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-[#397454]">Your plan</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-[-0.025em]">Current goals</h2>
          </div>
          {goals ? (
            <span className="rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-[#526158]">
              {goals.length} {goals.length === 1 ? "goal" : "goals"}
            </span>
          ) : null}
        </div>

        {goals === null ? (
          <div className="mt-6 rounded-2xl border border-[#e1c9be] bg-[#fff8f4] p-5 text-sm leading-6 text-[#805744]">
            Goals are unavailable. Start FastAPI on port 8000, then refresh this page.
          </div>
        ) : goals.length === 0 ? (
          <div className="mt-6 rounded-2xl border border-dashed border-[#c9d5cc] bg-white/70 p-8 text-center">
            <p className="font-medium text-[#405248]">No goals yet</p>
            <p className="mt-2 text-sm text-[#748078]">Your first goal will appear here after you add it.</p>
          </div>
        ) : (
          <ul className="mt-6 space-y-3">
            {goals.map((goal) => (
              <GoalCard key={goal.id} goal={goal} />
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
