import Link from "next/link";

import { ResumeReviewForm } from "@/components/resume-review-form";
import { getDocuments } from "@/lib/documents";
import { formatTimestamp } from "@/lib/format";
import { getResumeReviews } from "@/lib/resume-reviews";

export default async function ResumeReviewsPage() {
  const [documents, reviews] = await Promise.all([
    getDocuments(),
    getResumeReviews(),
  ]);
  const readyDocuments = (documents ?? []).filter(
    (document) => document.status === "ready",
  );
  const filenames = new Map(
    (documents ?? []).map((document) => [document.id, document.original_filename]),
  );

  return (
    <main className="min-h-screen bg-[#f5f7f2] text-[#16251d]">
      <header className="border-b border-[#dfe5dc] bg-[#fbfcf8]/90">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
          <Link className="flex items-center gap-3" href="/">
            <span className="grid size-10 place-items-center rounded-xl bg-[#173d2c] text-sm font-bold text-white">CO</span>
            <span>
              <span className="block text-lg font-semibold leading-none">CareerOS</span>
              <span className="mt-1 block text-xs text-[#617068]">Resume review</span>
            </span>
          </Link>
          <Link className="text-sm font-semibold text-[#397454] hover:text-[#173d2c]" href="/documents">
            Manage documents
          </Link>
        </div>
      </header>

      <div className="mx-auto grid max-w-5xl gap-6 px-6 py-12 lg:grid-cols-[0.85fr_1.15fr]">
        <section className="rounded-3xl border border-[#dbe2dc] bg-[#fbfcf9] p-6 sm:p-8">
          <p className="text-sm font-medium text-[#397454]">Focused feedback</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-[-0.03em]">Review your resume</h1>
          <p className="mt-3 text-sm leading-6 text-[#69766e]">
            Get evidence-based strengths, gaps, and rewrites for a specific role.
          </p>
          <div className="mt-7">
            {documents === null ? (
              <p className="text-sm text-[#a14f3b]">Documents are unavailable. Start FastAPI, then refresh.</p>
            ) : readyDocuments.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-[#c9d5cc] bg-white/70 p-6 text-sm leading-6 text-[#69766e]">
                Upload and successfully index a resume before requesting a review.{" "}
                <Link className="font-semibold text-[#397454]" href="/documents">Upload a document →</Link>
              </div>
            ) : (
              <ResumeReviewForm documents={readyDocuments} />
            )}
          </div>
        </section>

        <section className="rounded-3xl border border-[#dbe2dc] bg-[#eef3ed] p-6 sm:p-8">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-[#397454]">Saved analysis</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.025em]">Review history</h2>
            </div>
            {reviews ? <span className="rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-[#526158]">{reviews.length} reviews</span> : null}
          </div>

          {reviews === null ? (
            <div className="mt-6 rounded-2xl border border-[#e1c9be] bg-[#fff8f4] p-5 text-sm text-[#805744]">Reviews are unavailable. Start FastAPI, then refresh.</div>
          ) : reviews.length === 0 ? (
            <div className="mt-6 rounded-2xl border border-dashed border-[#c9d5cc] bg-white/70 p-8 text-center">
              <p className="font-medium text-[#405248]">No reviews yet</p>
              <p className="mt-2 text-sm text-[#748078]">Your first structured review will appear here.</p>
            </div>
          ) : (
            <ul className="mt-6 space-y-3">
              {reviews.map((review) => (
                <li key={review.id}>
                  <Link href={`/resume-reviews/${review.id}`} className="block rounded-2xl border border-[#dce4dd] bg-white p-5 transition hover:border-[#92a99a]">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="font-semibold text-[#203329]">{filenames.get(review.document_id) ?? "Uploaded resume"}</p>
                        <p className="mt-1 text-sm text-[#69766e]">{review.target_role ?? "General software engineering review"}</p>
                      </div>
                      <span className="rounded-full bg-[#e3ede5] px-2.5 py-1 text-xs font-semibold capitalize text-[#315f44]">{review.status}</span>
                    </div>
                    <p className="mt-3 text-xs text-[#7a877f]">{formatTimestamp(review.created_at)}</p>
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
