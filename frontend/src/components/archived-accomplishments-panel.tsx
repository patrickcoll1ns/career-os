import { deleteAccomplishmentAction } from "@/app/actions/accomplishments";
import { AccomplishmentArchiveControl } from "@/components/accomplishment-archive-control";
import { ConfirmDeleteControl } from "@/components/confirm-delete-control";
import {
  getArchivedAccomplishments,
  type Accomplishment,
} from "@/lib/accomplishments";
import { formatDate } from "@/lib/format";

function ArchivedAccomplishmentCard({
  accomplishment,
}: {
  accomplishment: Accomplishment;
}) {
  return (
    <li className="rounded-2xl border border-[#dce4dd] bg-white p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-semibold text-[#203329]">{accomplishment.title}</h3>
          {accomplishment.description ? (
            <p className="mt-2 text-sm leading-6 text-[#69766e]">
              {accomplishment.description}
            </p>
          ) : null}
        </div>
        <span className="shrink-0 rounded-full bg-[#eceeec] px-2.5 py-1 text-xs font-semibold text-[#5c665f]">
          Archived
        </span>
      </div>
      <p className="mt-4 text-xs font-medium text-[#7a877f]">
        {formatDate(accomplishment.achieved_on, "No date recorded")}
      </p>
      <AccomplishmentArchiveControl
        accomplishmentId={accomplishment.id}
        mode="restore"
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

export async function ArchivedAccomplishmentsPanel() {
  const archived = await getArchivedAccomplishments();

  if (!archived || archived.length === 0) {
    return null;
  }

  return (
    <section
      className="mt-10 rounded-3xl border border-[#dbe2dc] bg-[#fbfcf9] p-6 sm:p-8"
      aria-labelledby="archived-accomplishments-heading"
    >
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-[#397454]">Set aside</p>
          <h2
            id="archived-accomplishments-heading"
            className="mt-2 text-2xl font-semibold tracking-[-0.025em]"
          >
            Archived accomplishments
          </h2>
        </div>
        <span className="rounded-full bg-[#eef3ed] px-3 py-1.5 text-xs font-semibold text-[#526158]">
          {archived.length} {archived.length === 1 ? "entry" : "entries"}
        </span>
      </div>

      <ul className="mt-6 space-y-3">
        {archived.map((accomplishment) => (
          <ArchivedAccomplishmentCard
            key={accomplishment.id}
            accomplishment={accomplishment}
          />
        ))}
      </ul>
    </section>
  );
}
