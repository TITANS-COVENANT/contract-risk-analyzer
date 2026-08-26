"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import ClauseCard from "@/components/ClauseCard";
import ContractOverview from "@/components/ContractOverview";
import DisclaimerBanner from "@/components/DisclaimerBanner";
import FileUpload from "@/components/FileUpload";
import LoadingState from "@/components/LoadingState";
import RiskSummary from "@/components/RiskSummary";
import { analyzeContract, fetchHealth, getApiBaseUrl } from "@/lib/api";
import { exportAnalysisPdf } from "@/lib/exportReport";
import type { AnalysisResponse, HealthResponse, RiskLevel } from "@/lib/types";

type RiskFilter = "ALL" | RiskLevel;

const RISK_ORDER: Record<RiskLevel, number> = {
  HIGH: 0,
  MEDIUM: 1,
  LOW: 2,
};

export default function AnalyzePage() {
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [selectedName, setSelectedName] = useState<string | null>(null);
  const [filter, setFilter] = useState<RiskFilter>("ALL");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchHealth()
      .then((payload) => {
        if (!cancelled) {
          setHealth(payload);
          setHealthError(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setHealth(null);
          setHealthError(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const onFile = useCallback(async (file: File) => {
    setError(null);
    setResult(null);
    setFilter("ALL");
    setSelectedName(file.name);
    setLoading(true);
    try {
      const analysis = await analyzeContract(file);
      setResult(analysis);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unexpected analysis error.";
      setError(
        `${message} (API: ${getApiBaseUrl()}). Ensure the backend is running.`,
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const onReset = useCallback(() => {
    setResult(null);
    setError(null);
    setSelectedName(null);
    setFilter("ALL");
  }, []);

  const onExport = useCallback(async () => {
    if (!result) return;
    setExporting(true);
    try {
      await exportAnalysisPdf(result);
    } catch {
      setError("Could not export the PDF report. Please try again.");
    } finally {
      setExporting(false);
    }
  }, [result]);

  const sortedClauses = useMemo(() => {
    if (!result) return [];
    return result.clauses
      .slice()
      .sort((a, b) => RISK_ORDER[a.risk_level] - RISK_ORDER[b.risk_level]);
  }, [result]);

  const filteredClauses = useMemo(() => {
    if (filter === "ALL") return sortedClauses;
    return sortedClauses.filter((clause) => clause.risk_level === filter);
  }, [filter, sortedClauses]);

  const filterCounts = useMemo(() => {
    if (!result) {
      return { ALL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
    }
    return {
      ALL: result.summary.total_clauses,
      HIGH: result.summary.high,
      MEDIUM: result.summary.medium,
      LOW: result.summary.low,
    };
  }, [result]);

  return (
    <div className="app-shell">
      <DisclaimerBanner />

      <section className="panel">
        <div className="panel-head">
          <div>
            <h1>Analyze a contract</h1>
            <p>
              Upload an English PDF. Nothing is saved on the server after the
              request finishes.
            </p>
          </div>
          <div className="status-stack">
            {healthError ? (
              <span className="status-pill warn">Backend offline</span>
            ) : health ? (
              <>
                <span className="status-pill ok">API online</span>
                <span className="status-pill">
                  {health.llm_configured
                    ? `LLM · ${health.llm_provider}`
                    : "LLM offline fallback"}
                </span>
                <span className="status-pill">
                  {health.fine_tuned
                    ? "Fine-tuned Legal-BERT"
                    : health.model_loaded
                      ? "Legal-BERT loaded"
                      : "Keyword mode"}
                </span>
                <span className="status-pill">{health.classifier_labels} categories</span>
              </>
            ) : (
              <span className="status-pill">Checking API…</span>
            )}
          </div>
        </div>

        <FileUpload
          disabled={loading}
          selectedName={selectedName}
          onFile={onFile}
        />

        {loading ? <LoadingState /> : null}
        {error ? <div className="error">{error}</div> : null}

        {result && !loading ? (
          <div className="analyze-actions">
            <button type="button" className="btn btn-ghost btn-sm" onClick={onReset}>
              Analyze another file
            </button>
          </div>
        ) : null}
      </section>

      {result && !loading ? (
        <div className="results-stack">
          <RiskSummary
            filename={result.filename}
            summary={result.summary}
            clauses={result.clauses}
            onExport={onExport}
            exporting={exporting}
          />

          <ContractOverview metadata={result.document_metadata} />

          {result.processing_notes.length > 0 ? (
            <div className="notes-card">
              <h3>Processing notes</h3>
              <ul className="notes-list">
                {result.processing_notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </div>
          ) : null}

          <p className="result-disclaimer">{result.disclaimer}</p>

          <div className="results-toolbar">
            <div>
              <h2>Clauses by risk</h2>
              <p className="muted">
                Showing {filteredClauses.length} of {result.summary.total_clauses}
              </p>
            </div>
            <div className="filter-row" role="tablist" aria-label="Filter by risk">
              {(["ALL", "HIGH", "MEDIUM", "LOW"] as const).map((level) => (
                <button
                  key={level}
                  type="button"
                  role="tab"
                  aria-selected={filter === level}
                  className={`filter-chip${filter === level ? " active" : ""} ${level.toLowerCase()}`}
                  onClick={() => setFilter(level)}
                >
                  {level === "ALL" ? "All" : level}
                  <span>{filterCounts[level]}</span>
                </button>
              ))}
            </div>
          </div>

          {filteredClauses.length > 0 ? (
            <div className="clause-list">
              {filteredClauses.map((clause) => (
                <ClauseCard key={clause.id} clause={clause} />
              ))}
            </div>
          ) : (
            <div className="empty-state">
              No clauses match this filter. Try another risk level.
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
