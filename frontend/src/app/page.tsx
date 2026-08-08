import Link from "next/link";
import { Suspense } from "react";

import { AccomplishmentsPanel } from "@/components/accomplishments-panel";
import { AccomplishmentsPanelFallback } from "@/components/accomplishments-panel-fallback";
import { ApiStatus, ApiStatusFallback } from "@/components/api-status";
import { ArchivedGoalsPanel } from "@/components/archived-goals-panel";
import { GoalsPanel } from "@/components/goals-panel";
import { GoalsPanelFallback } from "@/components/goals-panel-fallback";

const focusAreas = [
  {
    title: "Career copilot",
    description: "Get guidance grounded in your goals and accomplishments.",
    action: "Start a conversation",
    href: "/chat",
  },
  {
    title: "Resume review",
    description: "Turn your experience into clear, evidence-based resume feedback.",
    action: "Review your resume",
    href: null,
  },
  {
    title: "Interview practice",
    description: "Practice role-specific questions and learn from structured feedback.",
    action: "Plan an interview",
    href: null,
  },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-[#f5f7f2] text-[#16251d]">
      <header className="border-b border-[#dfe5dc] bg-[#fbfcf8]/90">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5 lg:px-8">
          <a className="flex items-center gap-3" href="#top" aria-label="CareerOS home">
            <span className="grid size-10 place-items-center rounded-xl bg-[#173d2c] text-sm font-bold text-white">
              CO
            </span>
            <span>
              <span className="block text-lg font-semibold leading-none">CareerOS</span>
              <span className="mt-1 block text-xs text-[#617068]">Your career, with context</span>
            </span>
          </a>
          <span className="rounded-full border border-[#cfd8d1] bg-white px-3 py-1.5 text-xs font-medium text-[#526158]">
            MVP in progress
          </span>
        </div>
      </header>

      <div id="top" className="mx-auto max-w-6xl px-6 py-12 lg:px-8 lg:py-20">
        <section className="grid gap-10 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
          <div>
            <p className="mb-4 text-sm font-semibold uppercase tracking-[0.18em] text-[#397454]">
              AI-powered career workspace
            </p>
            <h1 className="max-w-3xl text-4xl font-semibold tracking-[-0.04em] sm:text-5xl lg:text-6xl">
              Make your next career move with the full story in view.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-[#58675f]">
              CareerOS brings your goals, accomplishments, and conversations together so your guidance becomes more useful over time.
            </p>
          </div>

          <aside className="rounded-3xl border border-[#d9e1da] bg-white p-6 shadow-[0_18px_60px_rgba(28,61,43,0.08)]">
            <div className="flex items-center justify-between gap-4">
              <p className="font-semibold">Today&apos;s focus</p>
              <Suspense fallback={<ApiStatusFallback />}>
                <ApiStatus />
              </Suspense>
            </div>
            <p className="mt-5 text-2xl font-medium tracking-[-0.02em]">
              What would make this week feel like progress?
            </p>
            <Link
              href="/chat"
              className="mt-6 block rounded-2xl bg-[#eef3ed] p-4 text-sm leading-6 text-[#4f6156] transition hover:bg-[#e4ede5]"
            >
              Talk it through with your career copilot{" "}
              <span aria-hidden="true">→</span>
            </Link>
          </aside>
        </section>

        <section className="mt-16" aria-labelledby="workspace-heading">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-[#397454]">Your workspace</p>
              <h2 id="workspace-heading" className="mt-2 text-2xl font-semibold tracking-[-0.025em]">
                One place to keep moving forward
              </h2>
            </div>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {focusAreas.map((area, index) => {
              const cardClassName =
                "group rounded-3xl border border-[#dbe2dc] bg-[#fbfcf9] p-6 transition hover:-translate-y-1 hover:border-[#b8cabd] hover:shadow-[0_14px_40px_rgba(28,61,43,0.08)]";
              const cardContent = (
                <>
                  <span className="grid size-9 place-items-center rounded-full bg-[#e3ede5] text-sm font-semibold text-[#315f44]">
                    0{index + 1}
                  </span>
                  <h3 className="mt-8 text-xl font-semibold">{area.title}</h3>
                  <p className="mt-3 min-h-18 text-sm leading-6 text-[#65736b]">{area.description}</p>
                  <p className="mt-6 text-sm font-semibold text-[#315f44]">
                    {area.action} <span aria-hidden="true">→</span>
                  </p>
                </>
              );

              return area.href ? (
                <Link key={area.title} href={area.href} className={cardClassName}>
                  {cardContent}
                </Link>
              ) : (
                <article key={area.title} className={cardClassName}>
                  {cardContent}
                </article>
              );
            })}
          </div>
        </section>

        <Suspense fallback={<GoalsPanelFallback />}>
          <GoalsPanel />
        </Suspense>

        <Suspense fallback={null}>
          <ArchivedGoalsPanel />
        </Suspense>

        <Suspense fallback={<AccomplishmentsPanelFallback />}>
          <AccomplishmentsPanel />
        </Suspense>
      </div>
    </main>
  );
}
