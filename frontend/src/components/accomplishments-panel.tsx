import { deleteAccomplishmentAction } from "@/app/actions/accomplishments";
import { AccomplishmentArchiveControl } from "@/components/accomplishment-archive-control";
import { AccomplishmentForm } from "@/components/accomplishment-form";
import { ConfirmDeleteControl } from "@/components/confirm-delete-control";
import { getAccomplishments, type Accomplishment } from "@/lib/accomplishments";
import { formatDate } from "@/lib/format";

/** How many of the newest entries stay expanded on the dashboard. */
const RECENT_LIMIT = 5;

function AccomplishmentCard({ accomplishment }: { accomplishment: Accomplishment }) {
  return (
    <li className="rounded-2xl border border-[#dce4dd] bg-white p-5">
      <h3 className="font-semibold text-[#203329]">{accomplishment.title}</h3>
      {accomplishment.description ? (
        <p className="mt-2 text-sm leading-6 text-[#69766e]">{accomplishment.description}</p>
      ) : null}
      <p className="mt-4 text-xs font-medium text-[#7a877f]">
        {formatDate(accomplishment.achieved_on, "No date recorded")}
      </p>
      <AccomplishmentArchiveControl
        accomplishmentId={accomplishment.id}
        mode="archive"
      />
      <ConfirmDeleteControl
        action={deleteAccomplishmentAction}
        idField="accomplishmentId"
        id={accomplishment.id}
        label="accomplishment"
      />
    </li>
  );
}

export async function AccomplishmentsPanel() {
  const accomplishments = await getAccomplishments();
  const recent = accomplishments?.slice(0, RECENT_LIMIT) ?? [];
  const earlier = accomplishments?.slice(RECENT_LIMIT) ?? [];

  return (
    <section
      className="mt-16 grid gap-6 lg:grid-cols-[0.85fr_1.15fr]"
      aria-labelledby="accomplishments-heading"
    >
      <div className="rounded-3xl border border-[#dbe2dc] bg-[#fbfcf9] p-6 sm:p-8">
        <p className="text-sm font-medium text-[#397454]">Record progress</p>
        <h2
          id="accomplishments-heading"
          className="mt-2 text-2xl font-semibold tracking-[-0.025em]"
        >
          Log an accomplishment
        </h2>
        <p className="mt-3 text-sm leading-6 text-[#69766e]">
          Capture a win while it&apos;s fresh so it&apos;s ready when you need to tell your story.
        </p>
        <div className="mt-7">
          <AccomplishmentForm />
        </div>
      </div>

      <div className="rounded-3xl border border-[#dbe2dc] bg-[#eef3ed] p-6 sm:p-8">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-[#397454]">Your journal</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-[-0.025em]">Accomplishments</h2>
          </div>
          {accomplishments ? (
            <span className="rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-[#526158]">
              {accomplishments.length} {accomplishments.length === 1 ? "entry" : "entries"}
            </span>
          ) : null}
        </div>

        {accomplishments === null ? (
          <div className="mt-6 rounded-2xl border border-[#e1c9be] bg-[#fff8f4] p-5 text-sm leading-6 text-[#805744]">
            Accomplishments are unavailable. Start FastAPI on port 8000, then refresh this page.
          </div>
        ) : accomplishments.length === 0 ? (
          <div className="mt-6 rounded-2xl border border-dashed border-[#c9d5cc] bg-white/70 p-8 text-center">
            <p className="font-medium text-[#405248]">No accomplishments yet</p>
            <p className="mt-2 text-sm text-[#748078]">Your first entry will appear here after you add it.</p>
          </div>
        ) : (
          <>
            <ul className="mt-6 space-y-3">
              {recent.map((accomplishment) => (
                <AccomplishmentCard key={accomplishment.id} accomplishment={accomplishment} />
              ))}
            </ul>

            {earlier.length > 0 ? (
              <details className="group mt-4 rounded-2xl border border-[#dce4dd] bg-white/70 p-4">
                <summary className="cursor-pointer list-none text-sm font-semibold text-[#405248] transition hover:text-[#173d2c]">
                  <span className="group-open:hidden">
                    Show {earlier.length} earlier{" "}
                    {earlier.length === 1 ? "entry" : "entries"}
                  </span>
                  <span className="hidden group-open:inline">Hide earlier entries</span>
                </summary>
                <ul className="mt-4 space-y-3">
                  {earlier.map((accomplishment) => (
                    <AccomplishmentCard key={accomplishment.id} accomplishment={accomplishment} />
                  ))}
                </ul>
              </details>
            ) : null}
          </>
        )}
      </div>
    </section>
  );
}
