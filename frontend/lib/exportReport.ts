import type { AnalysisResponse } from "./types";

/**
 * Build a simple multi-page PDF risk report in the browser.
 * Lazy-loads jspdf so the analyze page stays light until export is used.
 */
export async function exportAnalysisPdf(
  result: AnalysisResponse,
): Promise<void> {
  const { jsPDF } = await import("jspdf");
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const margin = 48;
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const maxWidth = pageWidth - margin * 2;
  let y = margin;

  const ensureSpace = (needed: number) => {
    if (y + needed > pageHeight - margin) {
      doc.addPage();
      y = margin;
    }
  };

  const writeWrapped = (
    text: string,
    options: { size?: number; bold?: boolean; color?: [number, number, number] } = {},
  ) => {
    const size = options.size ?? 11;
    doc.setFont("helvetica", options.bold ? "bold" : "normal");
    doc.setFontSize(size);
    if (options.color) {
      doc.setTextColor(...options.color);
    } else {
      doc.setTextColor(20, 28, 45);
    }
    const lines = doc.splitTextToSize(text, maxWidth);
    ensureSpace(lines.length * (size + 4) + 4);
    doc.text(lines, margin, y);
    y += lines.length * (size + 4) + 6;
  };

  writeWrapped("ClauseGuard — Contract Risk Report", {
    size: 18,
    bold: true,
    color: [31, 79, 214],
  });
  writeWrapped(`File: ${result.filename}`, { size: 11, bold: true });
  writeWrapped(
    `Clauses: ${result.summary.total_clauses}  ·  High: ${result.summary.high}  ·  Medium: ${result.summary.medium}  ·  Low: ${result.summary.low}`,
  );
  writeWrapped(result.disclaimer, { size: 9, color: [92, 102, 122] });

  const metadataEntries = Object.entries(result.document_metadata).filter(
    ([, value]) => Boolean(value),
  );
  if (metadataEntries.length > 0) {
    writeWrapped("Contract overview", { size: 12, bold: true });
    for (const [key, value] of metadataEntries) {
      const label = key.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
      writeWrapped(`${label}: ${value}`, { size: 10 });
    }
  }

  if (result.processing_notes.length > 0) {
    writeWrapped("Processing notes", { size: 12, bold: true });
    for (const note of result.processing_notes) {
      writeWrapped(`• ${note}`, { size: 10, color: [92, 102, 122] });
    }
  }

  const sorted = result.clauses.slice().sort((a, b) => {
    const order = { HIGH: 0, MEDIUM: 1, LOW: 2 } as const;
    return order[a.risk_level] - order[b.risk_level];
  });

  for (const clause of sorted) {
    ensureSpace(80);
    y += 6;
    writeWrapped(`#${clause.id} · ${clause.category} · ${clause.risk_level}`, {
      size: 13,
      bold: true,
    });
    writeWrapped(
      `Confidence ${(clause.confidence * 100).toFixed(0)}%${
        clause.llm_available ? " · LLM explanation" : " · Offline explanation"
      }`,
      { size: 9, color: [92, 102, 122] },
    );

    if (clause.risk_reasons.length > 0) {
      writeWrapped(`Why: ${clause.risk_reasons.join("; ")}`, { size: 10 });
    }
    writeWrapped("Plain English", { size: 10, bold: true });
    writeWrapped(clause.plain_english || "No explanation available.", {
      size: 10,
    });
    if (clause.suggested_alternative) {
      writeWrapped("Suggested alternative", { size: 10, bold: true });
      writeWrapped(clause.suggested_alternative, { size: 10 });
    }
    writeWrapped("Original text", { size: 10, bold: true });
    writeWrapped(clause.original_text, { size: 9, color: [42, 51, 72] });
  }

  const safeName = result.filename.replace(/\.pdf$/i, "") || "contract";
  doc.save(`${safeName}-risk-report.pdf`);
}

/**
 * Build a corrected contract PDF where HIGH/MEDIUM clauses are replaced
 * with their LLM-suggested alternatives. LOW-risk clauses keep original text.
 */
export async function exportCorrectedPdf(
  result: AnalysisResponse,
): Promise<void> {
  const { jsPDF } = await import("jspdf");
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const margin = 48;
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const maxWidth = pageWidth - margin * 2;
  let y = margin;

  const ensureSpace = (needed: number) => {
    if (y + needed > pageHeight - margin) {
      doc.addPage();
      y = margin;
    }
  };

  const writeWrapped = (
    text: string,
    options: { size?: number; bold?: boolean; color?: [number, number, number] } = {},
  ) => {
    const size = options.size ?? 11;
    doc.setFont("helvetica", options.bold ? "bold" : "normal");
    doc.setFontSize(size);
    if (options.color) {
      doc.setTextColor(...options.color);
    } else {
      doc.setTextColor(20, 28, 45);
    }
    const lines = doc.splitTextToSize(text, maxWidth);
    ensureSpace(lines.length * (size + 4) + 4);
    doc.text(lines, margin, y);
    y += lines.length * (size + 4) + 6;
  };

  // Header
  writeWrapped("ClauseGuard — Corrected Contract", {
    size: 18,
    bold: true,
    color: [31, 79, 214],
  });
  writeWrapped(`Based on: ${result.filename}`, { size: 11, bold: true });
  writeWrapped(
    `${result.clauses.filter((c) => c.suggested_alternative && c.risk_level !== "LOW").length} clause(s) replaced with AI-suggested alternatives.`,
    { size: 10, color: [92, 102, 122] },
  );
  writeWrapped(
    "IMPORTANT: This is an AI-generated draft. Have a qualified lawyer review before signing.",
    { size: 9, color: [180, 60, 40] },
  );
  y += 8;

  // Reconstruct contract in original clause order
  const ordered = result.clauses.slice().sort((a, b) => a.id - b.id);

  for (const clause of ordered) {
    const hasAlternative =
      Boolean(clause.suggested_alternative) && clause.risk_level !== "LOW";

    ensureSpace(60);
    y += 4;

    // Clause label
    const label = hasAlternative
      ? `[${clause.category} — AI REPLACEMENT]`
      : `[${clause.category}]`;
    const labelColor: [number, number, number] = hasAlternative
      ? [31, 120, 80]   // green for replaced
      : [80, 90, 110];  // grey for unchanged
    writeWrapped(label, { size: 9, bold: true, color: labelColor });

    // Clause body
    const body = hasAlternative
      ? clause.suggested_alternative
      : clause.original_text;
    writeWrapped(body, { size: 11 });
    y += 4;
  }

  const safeName = result.filename.replace(/\.pdf$/i, "") || "contract";
  doc.save(`${safeName}-corrected.pdf`);
}
