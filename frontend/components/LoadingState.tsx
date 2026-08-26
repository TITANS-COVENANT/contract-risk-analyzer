"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

const STEPS = [
  "Parsing PDF",
  "Classifying clauses",
  "Scoring risk",
  "Simplifying language",
];

export default function LoadingState() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActiveStep((current) => (current + 1) % STEPS.length);
    }, 1600);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <motion.div
      className="loading"
      role="status"
      aria-live="polite"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <motion.div
        className="spinner-ring"
        animate={{ rotate: 360 }}
        transition={{ duration: 0.9, ease: "linear", repeat: Infinity }}
      />
      <strong>Analyzing contract…</strong>
      <p>This usually takes a moment depending on document length and model load.</p>
      <div className="steps" aria-hidden="true">
        {STEPS.map((step, index) => (
          <motion.span
            key={step}
            className={`step-pill${index === activeStep ? " active" : ""}${index < activeStep ? " done" : ""}`}
            animate={{ scale: index === activeStep ? 1.04 : 1 }}
            transition={{ duration: 0.25 }}
          >
            {step}
          </motion.span>
        ))}
      </div>
    </motion.div>
  );
}
