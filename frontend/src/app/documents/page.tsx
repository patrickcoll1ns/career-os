import Link from "next/link";

import { deleteDocumentAction } from "@/app/actions/documents";
import { ConfirmDeleteControl } from "@/components/confirm-delete-control";
import { DocumentUploadForm } from "@/components/document-upload-form";
import { getDocuments, type CareerDocument } from "@/lib/documents";
import { formatTimestamp } from "@/lib/format";

const statusStyles: Record<CareerDocument["status"], string> = {
  pending: "bg-[#f4efe0] text-[#7b672c]",
  processing: "bg-[#e7eef5] text-[#3e607d]",
  ready: "bg-[#e3ede5] text-[#315f44]",
  failed: "bg-[#f7e8e2] text-[#9a503c]",
};

function formatFileSize(sizeBytes: number) {
  if (sizeBytes < 1024) return `${sizeBytes} B`;
  if (sizeBytes < 1024 * 1024) return `${(sizeBytes / 1024).toFixed(1)} KB`;
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default async function DocumentsPage() {
  const documents = await getDocuments();

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
              <span className="mt-1 block text-xs text-[#617068]">Career documents</span>
            </span>
          </Link>
          <Link className="text-sm font-semibold text-[#397454] hover:text-[#173d2c]" href="/chat">
            Open career copilot
          </Link>
        </div>
      </header>

      <div className="mx-auto grid max-w-5xl gap-6 px-6 py-12 lg:grid-cols-[0.85fr_1.15fr]">
        <section className="rounded-3xl border border-[#dbe2dc] bg-[#fbfcf9] p-6 sm:p-8">
          <p className="text-sm font-medium text-[#397454]">Add context</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-[-0.03em]">
            Upload a career document
          </h1>
          <p className="mt-3 text-sm leading-6 text-[#69766e]">
            CareerOS extracts and indexes your document so the copilot can find
            relevant evidence instead of guessing.
          </p>
          <div className="mt-7">
            <DocumentUploadForm />
          </div>
        </section>

        <section className="rounded-3xl border border-[#dbe2dc] bg-[#eef3ed] p-6 sm:p-8">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-[#397454]">Indexed context</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.025em]">Documents</h2>
            </div>
            {documents ? (
              <span className="rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-[#526158]">
                {documents.length} {documents.length === 1 ? "document" : "documents"}
              </span>
            ) : null}
          </div>

          {documents === null ? (
            <div className="mt-6 rounded-2xl border border-[#e1c9be] bg-[#fff8f4] p-5 text-sm leading-6 text-[#805744]">
              Documents are unavailable. Start FastAPI and PostgreSQL, then
              refresh this page.
            </div>
          ) : documents.length === 0 ? (
            <div className="mt-6 rounded-2xl border border-dashed border-[#c9d5cc] bg-white/70 p-8 text-center">
              <p className="font-medium text-[#405248]">No documents uploaded</p>
              <p className="mt-2 text-sm text-[#748078]">
                Your resume or career notes will appear here after indexing.
              </p>
            </div>
          ) : (
            <ul className="mt-6 space-y-3">
              {documents.map((document) => (
                <li key={document.id} className="rounded-2xl border border-[#dce4dd] bg-white p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-[#203329]">
                        {document.original_filename}
                      </p>
                      <p className="mt-1 text-xs text-[#7a877f]">
                        {formatFileSize(document.size_bytes)} · uploaded {formatTimestamp(document.created_at)}
                      </p>
                    </div>
                    <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${statusStyles[document.status]}`}>
                      {document.status}
                    </span>
                  </div>
                  {document.error_message ? (
                    <p className="mt-3 text-sm leading-6 text-[#9a503c]">{document.error_message}</p>
                  ) : null}
                  <ConfirmDeleteControl
                    action={deleteDocumentAction}
                    idField="documentId"
                    id={document.id}
                    label="document"
                    confirmMessage="Remove this document permanently? Its extracted text, search index, and saved resume reviews are deleted with it."
                  />
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}
