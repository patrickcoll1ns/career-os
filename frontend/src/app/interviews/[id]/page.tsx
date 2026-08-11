import Link from "next/link";

import { InterviewAnswerForm } from "@/components/interview-answer-form";
import { formatTimestamp } from "@/lib/format";
import {
  getInterviewSession,
  type InterviewHighlight,
  type InterviewTurn,
  type TurnFeedback,
} from "@/lib/interviews";

function turnFeedback(turn: InterviewTurn): TurnFeedback | null {
  const { score, strengths, improvement } = turn.feedback;
  if (score === undefined || strengths === undefined || improvement === undefined) {
    return null;
  }
  return { score, strengths, improvement };
}

function ScoreBadge({ score }: { score: number }) {
  return (
    <span className="shrink-0 rounded-full bg-[#e3ede5] px-3 py-1 text-xs font-semibold text-[#315f44]">
      {score} / 5
    </span>
  );
}

function Highlights({
  title,
  items,
}: {
  title: string;
  items: InterviewHighlight[];
}) {
  if (items.length === 0) return null;

  return (
    <div className="mt-6">
      <h3 className="text-sm font-semibold uppercase tracking-[0.12em] text-[#6d7b73]">
        {title}
      </h3>
      <ul className="mt-3 space-y-3">
        {items.map((item, index) => (
          <li
            key={`${item.title}-${index}`}
            className="rounded-2xl bg-[#f5f7f2] p-4"
          >
            <p className="font-semibold text-[#203329]">{item.title}</p>
            <p className="mt-1.5 text-sm leading-6 text-[#69766e]">{item.detail}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default async function InterviewSessionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const session = await getInterviewSession(id);

  if (session === null) {
    return (
      <main className="min-h-screen bg-[#f5f7f2] text-[#16251d]">
        <div className="mx-auto max-w-4xl px-6 py-12">
          <div className="rounded-2xl border border-[#e1c9be] bg-[#fff8f4] p-5 text-sm text-[#805744]">
            This interview session is unavailable. Make sure FastAPI is running on
            port 8000, then refresh this page.
          </div>
          <Link
            className="mt-6 inline-block text-sm font-semibold text-[#397454]"
            href="/interviews"
          >
            ← All interviews
          </Link>
        </div>
      </main>
    );
  }

  const answeredCount = session.turns.filter((turn) => turn.answer !== null).length;
  const openTurn = session.turns.find((turn) => turn.answer === null) ?? null;

  return (
    <main className="min-h-screen bg-[#f5f7f2] text-[#16251d]">
      <header className="border-b border-[#dfe5dc] bg-[#fbfcf8]/90">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-5">
          <Link className="font-semibold text-[#173d2c]" href="/">
            CareerOS
          </Link>
          <Link className="text-sm font-semibold text-[#397454]" href="/interviews">
            All interviews
          </Link>
        </div>
      </header>

      <div className="mx-auto max-w-4xl space-y-6 px-6 py-12">
        <section className="rounded-3xl bg-[#173d2c] p-6 text-white sm:p-8">
          <p className="text-sm font-medium capitalize text-[#c8d9ce]">
            {session.interview_type} interview · {session.difficulty}
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-[-0.03em]">
            {session.target_role}
          </h1>
          <p className="mt-3 text-xs text-[#b5c9bc]">
            Started {formatTimestamp(session.created_at)} · {answeredCount} of{" "}
            {session.question_limit}{" "}
            {session.question_limit === 1 ? "question" : "questions"} answered
          </p>
          {session.error_message ? (
            <p className="mt-6 text-sm text-[#ffd8ca]">{session.error_message}</p>
          ) : null}
        </section>

        <ol className="space-y-4">
          {session.turns.map((turn) => {
            const feedback = turnFeedback(turn);

            return (
              <li
                key={turn.id}
                className="rounded-3xl border border-[#dbe2dc] bg-white p-6 sm:p-8"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#6d7b73]">
                      Question {turn.sequence_number}
                    </p>
                    <h2 className="mt-2 text-lg font-semibold leading-7 text-[#203329]">
                      {turn.question}
                    </h2>
                  </div>
                  {feedback ? <ScoreBadge score={feedback.score} /> : null}
                </div>

                {turn.answer ? (
                  <div className="mt-5 rounded-2xl bg-[#f5f7f2] p-5">
                    <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#6d7b73]">
                      Your answer
                    </p>
                    <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-[#46584d]">
                      {turn.answer}
                    </p>
                  </div>
                ) : null}

                {feedback ? (
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl border border-[#dce4dd] p-4">
                      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#397454]">
                        What worked
                      </p>
                      <p className="mt-2 text-sm leading-6 text-[#69766e]">
                        {feedback.strengths}
                      </p>
                    </div>
                    <div className="rounded-2xl border border-[#dce4dd] p-4">
                      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#8a6b3f]">
                        To improve
                      </p>
                      <p className="mt-2 text-sm leading-6 text-[#69766e]">
                        {feedback.improvement}
                      </p>
                    </div>
                  </div>
                ) : null}

                {session.status === "active" && openTurn?.id === turn.id ? (
                  <InterviewAnswerForm sessionId={session.id} />
                ) : null}
              </li>
            );
          })}
        </ol>

        {session.status === "completed" ? (
          <section className="rounded-3xl border border-[#dbe2dc] bg-[#eef3ed] p-6 sm:p-8">
            <p className="text-sm font-medium text-[#397454]">Session complete</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-[-0.025em]">
              Your debrief
            </h2>
            {session.summary ? (
              <p className="mt-4 text-base leading-7 text-[#46584d]">
                {session.summary}
              </p>
            ) : null}

            <Highlights title="Strengths" items={session.strengths} />
            <Highlights title="Improvements" items={session.improvements} />
            <Highlights
              title="What to learn next"
              items={session.learning_recommendations}
            />
          </section>
        ) : null}
      </div>
    </main>
  );
}
