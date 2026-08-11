import Link from "next/link";

import { getDocuments } from "@/lib/documents";
import { formatTimestamp } from "@/lib/format";
import { getResumeReview, type ReviewFinding } from "@/lib/resume-reviews";

function Findings({ title, items }: { title: string; items: ReviewFinding[] }) {
  return (
    <section className="rounded-3xl border border-[#dbe2dc] bg-white p-6 sm:p-8">
      <h2 className="text-xl font-semibold">{title}</h2>
      {items.length === 0 ? (
        <p className="mt-4 text-sm text-[#748078]">No items returned.</p>
      ) : (
        <ul className="mt-5 space-y-4">
          {items.map((item, index) => (
            <li key={`${item.title}-${index}`} className="rounded-2xl bg-[#f5f7f2] p-5">
              <h3 className="font-semibold text-[#203329]">{item.title}</h3>
              <p className="mt-2 text-sm leading-6 text-[#69766e]"><span className="font-semibold text-[#526158]">Evidence:</span> {item.evidence}</p>
              <p className="mt-2 text-sm leading-6 text-[#46584d]"><span className="font-semibold">Action:</span> {item.recommendation}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default async function ResumeReviewDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [review, documents] = await Promise.all([getResumeReview(id), getDocuments()]);
  const filename = documents?.find((document) => document.id === review?.document_id)?.original_filename;

  return (
    <main className="min-h-screen bg-[#f5f7f2] text-[#16251d]">
      <header className="border-b border-[#dfe5dc] bg-[#fbfcf8]/90">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-5">
          <Link className="font-semibold text-[#173d2c]" href="/">CareerOS</Link>
          <Link className="text-sm font-semibold text-[#397454]" href="/resume-reviews">All reviews</Link>
        </div>
      </header>

      <div className="mx-auto max-w-4xl px-6 py-12">
        {review === null ? (
          <div className="rounded-2xl border border-[#e1c9be] bg-[#fff8f4] p-5 text-sm text-[#805744]">This resume review is unavailable.</div>
        ) : (
          <div className="space-y-6">
            <section className="rounded-3xl bg-[#173d2c] p-6 text-white sm:p-8">
              <p className="text-sm font-medium text-[#c8d9ce]">{filename ?? "Uploaded resume"}</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-[-0.03em]">{review.target_role ?? "General resume review"}</h1>
              <p className="mt-3 text-xs text-[#b5c9bc]">Generated {formatTimestamp(review.created_at)}</p>
              {review.summary ? <p className="mt-6 text-base leading-7 text-[#eef4ef]">{review.summary}</p> : null}
              {review.error_message ? <p className="mt-6 text-sm text-[#ffd8ca]">{review.error_message}</p> : null}
            </section>

            <Findings title="Strengths to preserve" items={review.strengths} />
            <Findings title="Highest-impact gaps" items={review.gaps} />

            <section className="rounded-3xl border border-[#dbe2dc] bg-[#eef3ed] p-6 sm:p-8">
              <h2 className="text-xl font-semibold">Rewrite suggestions</h2>
              {review.rewrite_suggestions.length === 0 ? (
                <p className="mt-4 text-sm text-[#748078]">No rewrites returned.</p>
              ) : (
                <ul className="mt-5 space-y-5">
                  {review.rewrite_suggestions.map((suggestion, index) => (
                    <li key={`${suggestion.original}-${index}`} className="rounded-2xl border border-[#dce4dd] bg-white p-5">
                      <p className="text-sm leading-6 text-[#7a877f] line-through">{suggestion.original}</p>
                      <p className="mt-3 text-sm font-medium leading-6 text-[#203329]">{suggestion.rewrite}</p>
                      <p className="mt-3 text-xs leading-5 text-[#69766e]">{suggestion.rationale}</p>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
