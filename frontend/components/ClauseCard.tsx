"use client";

import { useState } from "react";
import type { ClauseResult } from "@/lib/types";

interface ClauseCardProps {
  clause: ClauseResult;
}

export default function ClauseCard({ clause }: ClauseCardProps) {
  const [showOriginal, setShowOriginal] = useState(false);
  const confidencePct = Math.round(clause.confidence * 100);

  return (
    <article className="clause-card" data-risk={clause.risk_level}>
      <div className="clause-head">
        <div className="clause-title">
          <strong>
            #{clause.id} · {clause.category}
          </strong>
          <div className="clause-meta-row">
            <span className="confidence-meter" title={`Classifier confidence: ${confidencePct}%`}>
              <span className="confidence-track">
                <span
                  className="confidence-fill"
                  style={{ width: `${Math.max(6, confidencePct)}%` }}
                />
              </span>
              {confidencePct}%
            </span>
            <span>·</span>
            <span>{clause.llm_available ? "LLM explanation" : "Offline explanation"}</span>
          </div>
        </div>
        <span className={`badge ${clause.risk_level}`}>{clause.risk_level}</span>
      </div>

      <div className="clause-body">
        {clause.risk_reasons.length > 0 ? (
          <div className="clause-block">
            <h4>Why this risk</h4>
            <div className="reasons">
              {clause.risk_reasons.map((reason) => (
                <span className="chip" key={reason}>
                  {reason}
                </span>
              ))}
            </div>
          </div>
        ) : null}

        <div className="clause-block plain">
          <h4>Plain English</h4>
          <p>{clause.plain_english || "No explanation available."}</p>
        </div>

        {clause.suggested_alternative ? (
          <div className="clause-block alt">
            <h4>Suggested alternative</h4>
            <p>{clause.suggested_alternative}</p>
          </div>
        ) : null}

        <div className="clause-block original">
          <div className="clause-block-head">
            <h4>Original text</h4>
            <button
              type="button"
              className="text-btn"
              onClick={() => setShowOriginal((open) => !open)}
              aria-expanded={showOriginal}
            >
              {showOriginal ? "Hide" : "Show"}
            </button>
          </div>
          {showOriginal ? <pre>{clause.original_text}</pre> : null}
        </div>
      </div>
    </article>
  );
}
