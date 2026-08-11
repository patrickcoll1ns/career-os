import Link from "next/link";

import { InterviewSetupForm } from "@/components/interview-setup-form";
import { formatTimestamp } from "@/lib/format";
import { getInterviewSessions, type InterviewStatus } from "@/lib/interviews";

const statusStyles: Record<InterviewStatus, string> = {
  active: "bg-[#e3ede5] text-[#315f44]",
  completed: "bg-[#dfe9f2] text-[#2f5573]",
  abandoned: "bg-[#f2e3dd] text-[#805744]",
};

export default async function InterviewsPage() {
  const sessions = await getInterviewSessions();

  return (
    <main className="min-h-screen bg-[#f5f7f2] text-[#16251d]">
      <header className="border-b border-[#dfe5dc] bg-[#fbfcf8]/90">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
          <Link className="flex items-center gap-3" href="/">
            <span className="grid size-10 place-items-center rounded-xl bg-[#173d2c] text-sm font-bold text-white">
              CO
            </span>
            <span>
              <span className="block text-lg font-semibold leading-none">CareerOS</span>
              <span className="mt-1 block text-xs text-[#617068]">Interview practice</span>
            </span>
          </Link>
          <Link
            className="text-sm font-semibold text-[#397454] hover:text-[#173d2c]"
            href="/"
          >
            Back to dashboard
          </Link>
        </div>
      </header>

      <div className="mx-auto grid max-w-5xl gap-6 px-6 py-12 lg:grid-cols-[0.85fr_1.15fr]">
        <section className="rounded-3xl border border-[#dbe2dc] bg-[#fbfcf9] p-6 sm:p-8">
          <p className="text-sm font-medium text-[#397454]">Practice out loud</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-[-0.03em]">
            Run a mock interview
          </h1>
          <p className="mt-3 text-sm leading-6 text-[#69766e]">
            Answer role-specific questions one at a time and get scored feedback on
            every response.
          </p>
          <div className="mt-7">
            <InterviewSetupForm />
          </div>
        </section>

        <section className="rounded-3xl border border-[#dbe2dc] bg-[#eef3ed] p-6 sm:p-8">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-[#397454]">Saved practice</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.025em]">
                Interview history
              </h2>
            </div>
            {sessions ? (
              <span className="rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-[#526158]">
                {sessions.length} {sessions.length === 1 ? "session" : "sessions"}
              </span>
            ) : null}
          </div>

          {sessions === null ? (
            <div className="mt-6 rounded-2xl border border-[#e1c9be] bg-[#fff8f4] p-5 text-sm text-[#805744]">
              Interviews are unavailable. Start FastAPI on port 8000, then refresh.
            </div>
          ) : sessions.length === 0 ? (
            <div className="mt-6 rounded-2xl border border-dashed border-[#c9d5cc] bg-white/70 p-8 text-center">
              <p className="font-medium text-[#405248]">No interviews yet</p>
              <p className="mt-2 text-sm text-[#748078]">
                Start one to practice for a specific role.
              </p>
            </div>
          ) : (
            <ul className="mt-6 space-y-3">
              {sessions.map((session) => (
                <li key={session.id}>
                  <Link
                    href={`/interviews/${session.id}`}
                    className="block rounded-2xl border border-[#dce4dd] bg-white p-5 transition hover:border-[#92a99a]"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="font-semibold text-[#203329]">
                          {session.target_role}
                        </p>
                        <p className="mt-1 text-sm capitalize text-[#69766e]">
                          {session.interview_type} · {session.difficulty} ·{" "}
                          {session.question_limit}{" "}
                          {session.question_limit === 1 ? "question" : "questions"}
                        </p>
                      </div>
                      <span
                        className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${statusStyles[session.status]}`}
                      >
                        {session.status}
                      </span>
                    </div>
                    <p className="mt-3 text-xs text-[#7a877f]">
                      {formatTimestamp(session.created_at)}
                    </p>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}
