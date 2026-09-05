"use client";

import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";
import DisclaimerBanner from "@/components/DisclaimerBanner";

const fadeUp = {
  hidden: { opacity: 0, y: 22 },
  show: { opacity: 1, y: 0 },
};

/* ── Mock data for the live demo animation ── */
const MOCK_CLAUSES = [
  { category: "Indemnification",       risk: "HIGH"   as const, reason: "Unlimited one-sided indemnification — contractor bears all risk" },
  { category: "Renewal Term",          risk: "MEDIUM" as const, reason: "Auto-renews annually; 90-day opt-out window required" },
  { category: "Non-Compete",           risk: "HIGH"   as const, reason: "2-year nationwide non-compete — very broad scope" },
  { category: "IP Ownership Assignment", risk: "HIGH" as const, reason: "All work product assigned to client; no carve-outs" },
  { category: "Governing Law",         risk: "LOW"    as const, reason: "Standard Delaware governing law — balanced" },
  { category: "Cap on Liability",      risk: "LOW"    as const, reason: "Mutual liability cap at fees paid — balanced" },
  { category: "Confidentiality",       risk: "MEDIUM" as const, reason: "Perpetual NDA with no sunset clause" },
];

const RISK_COLOR  = { HIGH: "var(--high)",      MEDIUM: "var(--medium-fg)", LOW: "var(--low)"      };
const RISK_BG     = { HIGH: "var(--high-bg)",   MEDIUM: "var(--medium-bg)", LOW: "var(--low-bg)"   };
const RISK_BORDER = { HIGH: "var(--high-line)", MEDIUM: "var(--medium-line)", LOW: "var(--low-line)" };

function LiveDemo() {
  const [visible, setVisible] = useState<number[]>([]);
  const [scanning, setScanning] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const tos: ReturnType<typeof setTimeout>[] = [];

    async function run() {
      while (!cancelled) {
        setVisible([]);
        setScanning(true);
        await new Promise<void>(r => { const t = setTimeout(r, 800); tos.push(t); });
        if (cancelled) return;
        setScanning(false);

        for (let i = 0; i < MOCK_CLAUSES.length; i++) {
          if (cancelled) return;
          const t = setTimeout(() => {
            if (!cancelled) setVisible(v => [...v, i]);
          }, i * 950);
          tos.push(t);
        }

        await new Promise<void>(r => {
          const t = setTimeout(r, MOCK_CLAUSES.length * 950 + 3500);
          tos.push(t);
        });
      }
    }

    run();
    return () => { cancelled = true; tos.forEach(clearTimeout); };
  }, []);

  const highCount = visible.filter(i => MOCK_CLAUSES[i].risk === "HIGH").length;

  return (
    <div className="mock-demo">
      <div className="mock-demo-header">
        <div className="mock-file-pill">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          Freelance_Agreement.pdf
        </div>
        <div className="mock-status" style={{ color: scanning ? "var(--medium-fg)" : visible.length === MOCK_CLAUSES.length ? "var(--low)" : "var(--muted)" }}>
          {scanning ? "◉ Scanning document…" : visible.length === MOCK_CLAUSES.length ? `◉ Complete — ${highCount} HIGH risk` : `◉ ${visible.length} / ${MOCK_CLAUSES.length} clauses`}
        </div>
      </div>

      <div className="mock-feed">
        {scanning && <div className="mock-scan-bar"><div className="mock-scan-sweep" /></div>}
        <AnimatePresence>
          {visible.map(idx => {
            const c = MOCK_CLAUSES[idx];
            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                className="mock-clause"
              >
                <div className="mock-clause-head">
                  <span className="mock-category">{c.category}</span>
                  <span className="mock-badge" style={{ color: RISK_COLOR[c.risk], background: RISK_BG[c.risk], border: `1px solid ${RISK_BORDER[c.risk]}` }}>
                    {c.risk}
                  </span>
                </div>
                <p className="mock-reason">{c.reason}</p>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}

/* ── Comparison data ── */
const COMPARE = [
  { feature: "Contract privacy",       cg: "Processed in memory — zero bytes stored ever",              llm: "Sent to third-party servers, may train future models" },
  { feature: "Domain model",           cg: "Legal-BERT fine-tuned on 510 real CUAD contracts",          llm: "General-purpose LLM with no legal specialization" },
  { feature: "Clause categories",      cg: "48 structured categories (41 CUAD + 7 extensions)",         llm: "Unstructured — varies by how you word the prompt" },
  { feature: "Risk scoring",           cg: "Consistent HIGH / MEDIUM / LOW with specific reasons",      llm: "Free-form text, no guaranteed structure or consistency" },
  { feature: "Reproducibility",        cg: "Same clause → same category and risk score, every time",   llm: "Output varies across sessions and model versions" },
  { feature: "Suggested alternatives", cg: "Structured, legally cautious alternative clauses",          llm: "Sometimes — no guarantee of legal accuracy" },
  { feature: "Hallucination guard",    cg: "Classifier confidence threshold — low confidence = Unknown", llm: "No guardrails on invented legal interpretations" },
  { feature: "Cost",                   cg: "Free — no account, no subscription",                        llm: "ChatGPT Plus $20/mo or per-token API cost" },
];

export default function HomePage() {
  return (
    <>
      <div className="section-inner" style={{ paddingTop: "1.5rem" }}>
        <DisclaimerBanner />
      </div>

      {/* ── Hero ── */}
      <section className="section-inner hero">
        <motion.div
          initial="hidden"
          animate="show"
          variants={fadeUp}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          <div className="eyebrow">Legal literacy for freelancers &amp; SMEs</div>
          <h1>
            See the risky clauses
            <br />
            <span className="dim">before you sign.</span>
          </h1>
          <p className="hero-lead">
            ClauseGuard runs a fine-tuned Legal-BERT classifier trained on 510 real contracts
            across 48 clause categories — structured risk scores, plain-English explanations,
            and suggested alternatives. In under 30 seconds. For free.
          </p>
          <div className="hero-actions">
            <Link className="btn btn-primary" href="/analyze">
              Analyze a contract
            </Link>
            <a className="btn btn-secondary" href="#vs">
              Why not ChatGPT?
            </a>
          </div>
          <div className="hero-meta">
            <span><i />48 clause categories</span>
            <span><i />Legal-BERT · fine-tuned on CUAD</span>
            <span><i />Zero storage</span>
            <span><i />Free, no account needed</span>
          </div>
        </motion.div>
      </section>

      {/* ── Stats strip ── */}
      <div className="section-inner">
        <motion.div
          className="stat-strip"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
        >
          {[
            { n: "79.9%", label: "Classification accuracy", sub: "CUAD validation set" },
            { n: "48",    label: "Clause categories",       sub: "41 CUAD + 7 extensions" },
            { n: "510",   label: "Real contracts trained on", sub: "CUAD expert-labeled" },
            { n: "0 bytes", label: "Contract data stored",  sub: "in-memory processing only" },
          ].map(s => (
            <div className="stat-strip-item" key={s.label}>
              <div className="stat-strip-n">{s.n}</div>
              <div className="stat-strip-label">{s.label}</div>
              <div className="stat-strip-sub">{s.sub}</div>
            </div>
          ))}
        </motion.div>
      </div>

      {/* ── Live demo ── */}
      <section className="band" id="demo">
        <div className="section-inner split-demo">
          <div className="split-text">
            <span className="band-eyebrow">Live preview</span>
            <h2 className="split-h2">
              Clause-by-clause,
              <br /><span className="dim">as it happens.</span>
            </h2>
            <p>
              Every paragraph is classified by the Legal-BERT model, scored by the
              risk engine, and explained in plain English — all in a single API call.
              The demo shows the real output format with mock data.
            </p>
            <div className="hero-actions" style={{ marginTop: "1.75rem" }}>
              <Link className="btn btn-primary" href="/analyze">
                Try with your contract
              </Link>
            </div>
          </div>
          <LiveDemo />
        </div>
      </section>

      {/* ── vs ChatGPT ── */}
      <section className="band band-dark" id="vs">
        <div className="section-inner">
          <div className="band-head">
            <span className="band-eyebrow" style={{ color: "var(--inverse-muted)" }}>Why not just use ChatGPT or Claude?</span>
            <h2>
              Purpose-built beats <span className="dim">general-purpose.</span>
            </h2>
            <p>
              Pasting a contract into a chat window gets you a conversation.
              ClauseGuard gets you a structured audit — with privacy guarantees,
              a domain-trained model, and consistent risk scores you can act on.
            </p>
          </div>
          <div className="compare-wrap">
            <table className="compare-table">
              <thead>
                <tr>
                  <th className="th-feat">Feature</th>
                  <th className="th-cg"><span className="th-cg-pill">ClauseGuard</span></th>
                  <th className="th-llm">ChatGPT / Claude</th>
                </tr>
              </thead>
              <tbody>
                {COMPARE.map(row => (
                  <tr key={row.feature}>
                    <td className="td-feat">{row.feature}</td>
                    <td className="td-cg"><span className="td-check">✓</span>{row.cg}</td>
                    <td className="td-llm"><span className="td-x">✕</span>{row.llm}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section className="band" id="how">
        <div className="section-inner">
          <div className="band-head">
            <span className="band-eyebrow">How it works</span>
            <h2>
              Three steps from PDF <span className="dim">to clarity.</span>
            </h2>
            <p>A focused pipeline built for non-lawyers — not a black-box "AI lawyer."</p>
          </div>
        </div>
        <div className="section-inner">
          <div className="feature-grid">
            {[
              {
                n: "01",
                title: "Sieve",
                body: "Segment the PDF and classify each paragraph across all 48 categories using Legal-BERT fine-tuned on 510 real CUAD contracts, blended with keyword signals for edge-case robustness.",
              },
              {
                n: "02",
                title: "Judge",
                body: "Score each clause HIGH, MEDIUM, or LOW risk using category priors and red-flag patterns — unlimited liability, one-sided indemnity, hidden auto-renewal, broad non-competes, and more.",
              },
              {
                n: "03",
                title: "Translator",
                body: "Get plain-English explanations and fairer alternative clause language via Llama 3.3, so you know exactly what to push back on before you sign.",
              },
            ].map(f => (
              <div className="feature" key={f.title}>
                <div className="feature-index">{f.n}</div>
                <h3>{f.title}</h3>
                <p>{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Model performance ── */}
      <section className="band band-alt" id="performance">
        <div className="section-inner">
          <div className="band-head">
            <span className="band-eyebrow">Model performance</span>
            <h2>
              Trained and evaluated on <span className="dim">real contracts.</span>
            </h2>
            <p>
              The classifier was fine-tuned on the official CUAD dataset —
              510 expert-annotated commercial contracts, 41 categories, 13,000+ labeled clauses —
              then evaluated on a held-out validation set.
            </p>
          </div>
          <div className="perf-grid">
            {[
              { value: "79.9%", label: "Overall accuracy",   note: "CUAD validation set" },
              { value: "0.699", label: "Macro F1 score",     note: "averaged across all 42 classes" },
              { value: "0.795", label: "Weighted F1 score",  note: "weighted by class frequency" },
              { value: "510",   label: "Training contracts", note: "CUAD expert-labeled dataset" },
            ].map(m => (
              <div className="perf-card" key={m.label}>
                <div className="perf-value">{m.value}</div>
                <div className="perf-label">{m.label}</div>
                <div className="perf-note">{m.note}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Trust / privacy ── */}
      <section className="band band-dark" id="privacy">
        <div className="section-inner">
          <div className="band-head">
            <span className="band-eyebrow" style={{ color: "var(--inverse-muted)" }}>Built to be trusted</span>
            <h2>
              Decision support, <span className="dim">not a replacement for a lawyer.</span>
            </h2>
          </div>
          <div className="trust-strip">
            <div className="trust-card">
              <h3>Built for careful review</h3>
              <p>
                ClauseGuard surfaces risk signals and readable explanations so
                you can decide what to negotiate — or what needs a lawyer.
              </p>
              <ul className="checklist">
                <li>Risk-ranked so high-priority clauses come first</li>
                <li>Original legalese kept alongside plain English</li>
                <li>Suggested alternatives for unbalanced terms</li>
                <li>Classifier confidence score on every result</li>
              </ul>
            </div>
            <div className="privacy-card">
              <h3>Privacy by design</h3>
              <p>
                Contract bytes are processed in memory for the request only —
                no permanent storage, no document archive, no account required.
              </p>
              <ul className="checklist">
                <li>No login — analyze immediately</li>
                <li>Request-scoped processing, nothing persisted</li>
                <li>Legal-information disclaimer on every result</li>
                <li>Open-source stack — auditable end to end</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="section-inner cta-band">
        <h2>Ready to review a contract?</h2>
        <p>Drop in a text-based English PDF and get a ranked risk report in under 30 seconds — free, no account needed.</p>
        <div className="hero-actions">
          <Link className="btn btn-primary" href="/analyze">
            Start analysis — it&apos;s free
          </Link>
          <a className="btn btn-secondary" href="#vs">
            See how it compares
          </a>
        </div>
      </section>
    </>
  );
}
