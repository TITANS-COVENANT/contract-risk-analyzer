"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import DisclaimerBanner from "@/components/DisclaimerBanner";

const fadeUp = {
  hidden: { opacity: 0, y: 22 },
  show: { opacity: 1, y: 0 },
};

export default function HomePage() {
  return (
    <>
      <div className="section-inner" style={{ paddingTop: "1.5rem" }}>
        <DisclaimerBanner />
      </div>

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
            Upload a service agreement or NDA. ClauseGuard classifies every
            clause across all 41 official CUAD categories, scores the risk,
            and translates legalese into plain English — so you know exactly
            what to negotiate.
          </p>
          <div className="hero-actions">
            <Link className="btn btn-primary" href="/analyze">
              Analyze a PDF
            </Link>
            <a className="btn btn-secondary" href="#how">
              How it works
            </a>
          </div>
          <div className="hero-meta">
            <span>
              <i /> English PDF contracts
            </span>
            <span>
              <i /> No permanent storage
            </span>
            <span>
              <i /> High / Medium / Low risk
            </span>
          </div>
        </motion.div>
      </section>

      <section className="band" id="how">
        <div className="section-inner">
          <div className="band-head">
            <span className="band-eyebrow">How it works</span>
            <h2>
              Three steps from PDF <span className="dim">to clarity.</span>
            </h2>
            <p>A focused pipeline built for freelancers and small businesses — not a black-box "AI lawyer."</p>
          </div>
        </div>
        <div className="section-inner">
          <div className="feature-grid">
            {[
              {
                n: "01",
                title: "Sieve",
                body: "Segment the PDF and classify each clause across all 41 official CUAD categories using a fine-tuned Legal-BERT classifier plus keyword signals.",
              },
              {
                n: "02",
                title: "Judge",
                body: "Score High, Medium, or Low risk from category priors and common red-flag patterns — unlimited liability, one-sided indemnity, hidden auto-renewal, and more.",
              },
              {
                n: "03",
                title: "Translator",
                body: "Get plain-English explanations and fairer alternative language so you know what to negotiate before you sign.",
              },
            ].map((f) => (
              <div className="feature" key={f.title}>
                <div className="feature-index">{f.n}</div>
                <h3>{f.title}</h3>
                <p>{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="band band-dark" id="privacy">
        <div className="section-inner">
          <div className="band-head">
            <span className="band-eyebrow">Built to be trusted</span>
            <h2>
              Decision support, <span className="dim">not a replacement for a lawyer.</span>
            </h2>
          </div>
          <div className="trust-strip">
            <div className="trust-card">
              <h3>Built for careful review</h3>
              <p>
                ClauseGuard surfaces risk signals and readable explanations so
                you can decide what needs a lawyer.
              </p>
              <ul className="checklist">
                <li>Risk ranked so high-priority clauses come first</li>
                <li>Original text kept alongside plain English</li>
                <li>Suggested alternatives for unbalanced terms</li>
              </ul>
            </div>
            <div className="privacy-card">
              <h3>Privacy by design</h3>
              <p>
                Contract bytes are processed in memory for the request only —
                no permanent storage, no document archive.
              </p>
              <ul className="checklist">
                <li>No account required to analyze</li>
                <li>Request-scoped processing only</li>
                <li>Clear legal-information disclaimer</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section className="section-inner cta-band">
        <h2>Ready to review a contract?</h2>
        <p>Drop in a text-based English PDF and get a ranked risk report in minutes.</p>
        <div className="hero-actions">
          <Link className="btn btn-primary" href="/analyze">
            Start analysis
          </Link>
        </div>
      </section>
    </>
  );
}
