export default function DisclaimerBanner() {
  return (
    <div className="disclaimer" role="note">
      <span className="disclaimer-icon" aria-hidden="true">
        !
      </span>
      <div>
        <strong>Legal information, not legal advice.</strong> This tool helps you
        spot potentially risky clauses and understand them in plain English. It
        is not a substitute for a qualified attorney. Do not sign important
        agreements based solely on automated analysis.
      </div>
    </div>
  );
}
