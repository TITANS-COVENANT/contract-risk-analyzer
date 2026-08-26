import type { DocumentMetadata } from "@/lib/types";

interface ContractOverviewProps {
  metadata: DocumentMetadata;
}

const FIELDS: Array<{ key: keyof DocumentMetadata; label: string }> = [
  { key: "document_name", label: "Document" },
  { key: "parties", label: "Parties" },
  { key: "agreement_date", label: "Agreement date" },
  { key: "effective_date", label: "Effective date" },
  { key: "expiration_date", label: "Expiration date" },
  { key: "governing_law", label: "Governing law" },
];

export default function ContractOverview({ metadata }: ContractOverviewProps) {
  const present = FIELDS.filter((f) => metadata[f.key]);
  if (present.length === 0) {
    return null;
  }

  return (
    <section className="panel results-panel" aria-label="Contract overview">
      <div className="panel-head">
        <div>
          <h1 style={{ fontSize: "1.15rem" }}>Contract overview</h1>
          <p>Facts extracted automatically — verify against the original document.</p>
        </div>
      </div>
      <div className="overview-grid">
        {present.map((f) => (
          <div className="overview-item" key={f.key}>
            <div className="k">{f.label}</div>
            <div className="v">{metadata[f.key]}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
