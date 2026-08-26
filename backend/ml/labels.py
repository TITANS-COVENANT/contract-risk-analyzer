"""CUAD clause labels and risk priors for freelancers/SMEs.

Reference: Hendrycks et al. (2021) CUAD — 41 expert-annotated clause
categories, verified against the official category list published at
github.com/The-Atticus-Project/cuad (category_descriptions.csv).

Taxonomy design:
- All 41 official CUAD categories are included, so the fine-tuned classifier
  (trained on CUAD-derived data — see notebooks/finetune_legal_bert_cuad.ipynb)
  can predict any of them directly with matching label strings.
- CUAD does NOT define a standalone "Indemnification", "Confidentiality", or
  general "Limitation of Liability" category, even though these are some of
  the most common and highest-stakes clauses in freelancer/SME contracts (and
  the proposal's own Appendix B walkthrough is an indemnification example).
  Seven EXTENSION categories cover this gap. They have no CUAD gold training
  data, so they are served by the keyword/prototype layer only — the hybrid
  classifier already falls back to keywords whenever the fine-tuned model's
  confidence is lower than a strong keyword match (see classifier.py).
- `kind` distinguishes pure document metadata (Document Name, Parties, and
  the three date fields) — which the pipeline routes into a "Contract
  Overview" panel instead of a risk-scored clause card — from every other
  category, which is treated as a risk clause. Renewal Term, Notice Period
  to Terminate Renewal, and Governing Law are classic "hidden gotcha"
  categories, so they stay risk-scored rather than being demoted to
  metadata, even though they are also convenient facts to surface.
"""

from __future__ import annotations

from typing import Dict, List, Literal, TypedDict

LabelKind = Literal["metadata", "risk"]


class LabelMeta(TypedDict):
    """Metadata for a clause category."""

    name: str
    kind: LabelKind
    base_risk: str  # LOW | MEDIUM | HIGH
    prototypes: List[str]
    keywords: List[str]


# --- 41 official CUAD categories, in the dataset's own order ---------------
_CUAD_LABELS: Dict[str, LabelMeta] = {
    "Document Name": {
        "name": "Document Name",
        "kind": "metadata",
        "base_risk": "LOW",
        "prototypes": [
            "This Service Agreement (the Agreement) is entered into by and between the parties below.",
        ],
        "keywords": ["agreement", "this agreement", "this contract", "master services agreement"],
    },
    "Parties": {
        "name": "Parties",
        "kind": "metadata",
        "base_risk": "LOW",
        "prototypes": [
            "This Agreement is made between Acme Inc, a Delaware corporation (Client), and Jane Doe (Contractor).",
        ],
        "keywords": ["by and between", "hereinafter referred to as", "client\" and \"contractor", "the parties"],
    },
    "Agreement Date": {
        "name": "Agreement Date",
        "kind": "metadata",
        "base_risk": "LOW",
        "prototypes": [
            "This Agreement is made and entered into as of January 1, 2026.",
        ],
        "keywords": ["entered into as of", "dated as of", "made and entered into on"],
    },
    "Effective Date": {
        "name": "Effective Date",
        "kind": "metadata",
        "base_risk": "LOW",
        "prototypes": [
            "This Agreement shall become effective on the Effective Date first written above.",
        ],
        "keywords": ["effective date", "shall become effective", "effective as of"],
    },
    "Expiration Date": {
        "name": "Expiration Date",
        "kind": "metadata",
        "base_risk": "LOW",
        "prototypes": [
            "This Agreement shall expire on December 31, 2027 unless earlier terminated.",
        ],
        "keywords": ["shall expire on", "expiration date", "expires on"],
    },
    "Renewal Term": {
        "name": "Renewal Term",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "This Agreement shall automatically renew for successive one-year terms unless either party provides notice of non-renewal.",
            "Following the initial term, this Agreement renews automatically for additional twelve-month periods.",
        ],
        "keywords": ["automatically renew", "auto-renew", "successive terms", "renewal term", "renews for"],
    },
    "Notice Period to Terminate Renewal": {
        "name": "Notice Period to Terminate Renewal",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "To prevent automatic renewal, either party must provide written notice at least ninety (90) days before the end of the then-current term.",
        ],
        "keywords": ["notice of non-renewal", "prior to the end of", "days before the expiration", "written notice of intent not to renew"],
    },
    "Governing Law": {
        "name": "Governing Law",
        "kind": "risk",
        "base_risk": "LOW",
        "prototypes": [
            "This agreement shall be governed by and construed in accordance with the laws of the State of Delaware without regard to conflict of laws principles.",
        ],
        "keywords": ["governing law", "governed by", "laws of the state of", "laws of", "jurisdiction", "venue", "exclusive jurisdiction"],
    },
    "Most Favored Nation": {
        "name": "Most Favored Nation",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Contractor agrees that the pricing offered to Client shall be no less favorable than pricing offered to any other customer for similar services.",
        ],
        "keywords": ["most favored nation", "no less favorable", "most favored customer", "best pricing"],
    },
    "Non-Compete": {
        "name": "Non-Compete",
        "kind": "risk",
        "base_risk": "HIGH",
        "prototypes": [
            "During the term and for twelve months thereafter the contractor shall not engage in any competing business.",
            "Employee agrees not to compete with the company within a geographic area for a period of time after termination.",
        ],
        "keywords": ["non-compete", "noncompete", "not compete", "competing business", "restraint of trade"],
    },
    "Exclusivity": {
        "name": "Exclusivity",
        "kind": "risk",
        "base_risk": "HIGH",
        "prototypes": [
            "Contractor shall provide services exclusively to the client and shall not perform similar services for competitors during the term.",
        ],
        "keywords": ["exclusivity", "exclusive basis", "exclusive provider", "sole provider", "exclusively to"],
    },
    "No-Solicit of Customers": {
        "name": "No-Solicit of Customers",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Contractor shall not solicit or accept business from any client of the Company for a period after termination.",
        ],
        "keywords": ["solicit clients", "solicit customers", "non-solicitation of customers", "shall not solicit any client"],
    },
    "Competitive Restriction Exception": {
        "name": "Competitive Restriction Exception",
        "kind": "risk",
        "base_risk": "LOW",
        "prototypes": [
            "Notwithstanding the foregoing non-compete provision, Contractor may continue to provide services to the pre-existing clients listed in Exhibit A.",
        ],
        "keywords": ["notwithstanding the foregoing", "shall not apply to", "exception to the restriction", "carve-out"],
    },
    "No-Solicit of Employees": {
        "name": "No-Solicit of Employees",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Contractor shall not solicit or hire any employee of the Company for twelve months following termination.",
        ],
        "keywords": ["solicit employees", "solicit or hire", "non-solicitation of employees", "hire any employee"],
    },
    "Non-Disparagement": {
        "name": "Non-Disparagement",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Neither party shall make any disparaging statement about the other party, its products, or its personnel.",
        ],
        "keywords": ["disparage", "disparaging statement", "non-disparagement", "negative statements about"],
    },
    "Termination for Convenience": {
        "name": "Termination for Convenience",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Either party may terminate this agreement for convenience upon thirty days written notice.",
            "Client may terminate immediately without cause and without further obligation.",
        ],
        "keywords": ["for convenience", "without cause", "terminate this agreement", "notice of termination", "immediate termination"],
    },
    "Rofr/Rofo/Rofn": {
        "name": "Rofr/Rofo/Rofn",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Before accepting an offer from a third party for similar services, Contractor shall first offer Client the right of first refusal on the same terms.",
        ],
        "keywords": ["right of first refusal", "right of first offer", "right of first negotiation", "first offer to"],
    },
    "Change of Control": {
        "name": "Change of Control",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "In the event of a change of control of either party, the other party may terminate this Agreement upon written notice.",
        ],
        "keywords": ["change of control", "merger, acquisition", "sale of substantially all assets", "acquired by"],
    },
    "Anti-Assignment": {
        "name": "Anti-Assignment",
        "kind": "risk",
        "base_risk": "LOW",
        "prototypes": [
            "Neither party may assign this agreement without the prior written consent of the other party except to an affiliate or successor.",
        ],
        "keywords": ["assignment", "may not assign", "shall not assign", "transfer this agreement", "prior written consent"],
    },
    "Revenue/Profit Sharing": {
        "name": "Revenue/Profit Sharing",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Client shall pay Contractor twenty percent (20%) of net revenue generated from the deliverables under this Agreement.",
        ],
        "keywords": ["revenue sharing", "profit sharing", "percentage of revenue", "percentage of net profit", "royalty"],
    },
    "Price Restrictions": {
        "name": "Price Restrictions",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Contractor shall not sell the same services to any other party at a lower price than offered to Client.",
        ],
        "keywords": ["price restriction", "minimum resale price", "not sell at a lower price", "pricing floor"],
    },
    "Minimum Commitment": {
        "name": "Minimum Commitment",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Client agrees to purchase a minimum of $10,000 in services from Contractor each calendar quarter.",
        ],
        "keywords": ["minimum commitment", "minimum purchase", "minimum spend", "minimum order quantity", "minimum volume"],
    },
    "Volume Restriction": {
        "name": "Volume Restriction",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Contractor's services under this Agreement shall not exceed 500 hours per year without Client's prior written approval.",
        ],
        "keywords": ["volume restriction", "shall not exceed", "capacity limit", "maximum volume"],
    },
    "IP Ownership Assignment": {
        "name": "IP Ownership Assignment",
        "kind": "risk",
        "base_risk": "HIGH",
        "prototypes": [
            "All work product and intellectual property created under this agreement shall be the exclusive property of the client as work made for hire.",
            "Contractor hereby assigns all right, title, and interest in inventions and copyrights to the company.",
        ],
        "keywords": ["work made for hire", "work for hire", "assigns all right", "intellectual property", "exclusive property of the client", "ownership of deliverables"],
    },
    "Joint IP Ownership": {
        "name": "Joint IP Ownership",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Any intellectual property jointly developed by the parties under this Agreement shall be jointly owned by both parties.",
        ],
        "keywords": ["jointly owned", "joint ownership", "co-owned", "jointly developed"],
    },
    "License Grant": {
        "name": "License Grant",
        "kind": "risk",
        "base_risk": "LOW",
        "prototypes": [
            "Contractor grants Client a non-exclusive license to use the deliverables solely for Client's internal business purposes.",
        ],
        "keywords": ["grants a license", "license to use", "hereby grants", "non-exclusive license"],
    },
    "Non-Transferable License": {
        "name": "Non-Transferable License",
        "kind": "risk",
        "base_risk": "LOW",
        "prototypes": [
            "The license granted herein is personal to Client and may not be transferred or sublicensed to any third party.",
        ],
        "keywords": ["non-transferable", "may not be transferred", "may not sublicense", "personal to"],
    },
    "Affiliate License-Licensor": {
        "name": "Affiliate License-Licensor",
        "kind": "risk",
        "base_risk": "LOW",
        "prototypes": [
            "The license granted by Contractor extends to Contractor's affiliates for the purposes of this Agreement.",
        ],
        "keywords": ["licensor's affiliates", "affiliates of the licensor", "extends to affiliates"],
    },
    "Affiliate License-Licensee": {
        "name": "Affiliate License-Licensee",
        "kind": "risk",
        "base_risk": "LOW",
        "prototypes": [
            "Client's affiliates may also use the licensed deliverables under the same terms as Client.",
        ],
        "keywords": ["licensee's affiliates", "affiliates of the licensee", "client's affiliates may"],
    },
    "Unlimited/All-You-Can-Eat-License": {
        "name": "Unlimited/All-You-Can-Eat-License",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Client is granted unlimited use of the licensed materials across an unlimited number of users and locations.",
        ],
        "keywords": ["unlimited use", "unlimited number of users", "all-you-can-eat", "without limitation on use"],
    },
    "Irrevocable or Perpetual License": {
        "name": "Irrevocable or Perpetual License",
        "kind": "risk",
        "base_risk": "HIGH",
        "prototypes": [
            "The license granted to Client under this Agreement is irrevocable and perpetual, surviving termination of this Agreement.",
        ],
        "keywords": ["irrevocable license", "perpetual license", "irrevocable and perpetual", "survives termination"],
    },
    "Source Code Escrow": {
        "name": "Source Code Escrow",
        "kind": "risk",
        "base_risk": "LOW",
        "prototypes": [
            "Contractor shall deposit the source code into escrow with a third-party escrow agent for release upon specified triggering events.",
        ],
        "keywords": ["source code escrow", "escrow agent", "deposit the source code", "escrow account"],
    },
    "Post-Termination Services": {
        "name": "Post-Termination Services",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Following termination, Contractor shall continue to provide transition assistance for up to ninety days at no additional charge.",
        ],
        "keywords": ["post-termination", "transition assistance", "following termination, contractor shall", "wind-down services"],
    },
    "Audit Rights": {
        "name": "Audit Rights",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Client shall have the right to audit contractor's books and records related to this agreement upon reasonable notice.",
        ],
        "keywords": ["audit", "inspect books", "books and records", "right to audit"],
    },
    "Uncapped Liability": {
        "name": "Uncapped Liability",
        "kind": "risk",
        "base_risk": "HIGH",
        "prototypes": [
            "Contractor's liability under this Agreement shall be unlimited and shall not be subject to any cap or limitation.",
        ],
        "keywords": ["unlimited liability", "no cap on liability", "uncapped", "without limitation, liable"],
    },
    "Cap on Liability": {
        "name": "Cap on Liability",
        "kind": "risk",
        "base_risk": "LOW",
        "prototypes": [
            "Total liability under this agreement shall not exceed the fees paid in the twelve months preceding the claim.",
        ],
        "keywords": ["limitation of liability", "cap on liability", "shall not exceed the fees paid", "aggregate liability", "in no event shall"],
    },
    "Liquidated Damages": {
        "name": "Liquidated Damages",
        "kind": "risk",
        "base_risk": "HIGH",
        "prototypes": [
            "In the event of a breach, the breaching party shall pay liquidated damages of $50,000 as agreed compensation.",
        ],
        "keywords": ["liquidated damages", "agreed compensation", "penalty of", "as liquidated damages and not as a penalty"],
    },
    "Warranty Duration": {
        "name": "Warranty Duration",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Contractor warrants the deliverables will be free of material defects for a period of ninety (90) days from delivery.",
            "Services are provided as is without warranty of any kind, express or implied, including merchantability and fitness for a particular purpose.",
        ],
        "keywords": ["warranty", "warranties", "as is", "merchantability", "fitness for a particular purpose", "warranty period"],
    },
    "Insurance": {
        "name": "Insurance",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Contractor shall maintain professional liability insurance with coverage of at least one million dollars and name client as additional insured.",
        ],
        "keywords": ["insurance", "liability insurance", "additional insured", "coverage of at least", "certificate of insurance"],
    },
    "Covenant Not to Sue": {
        "name": "Covenant Not to Sue",
        "kind": "risk",
        "base_risk": "HIGH",
        "prototypes": [
            "Contractor agrees never to sue Client for any claim arising out of or relating to this Agreement.",
        ],
        "keywords": ["covenant not to sue", "agrees never to sue", "waives the right to bring", "shall not initiate legal action"],
    },
    "Third Party Beneficiary": {
        "name": "Third Party Beneficiary",
        "kind": "risk",
        "base_risk": "LOW",
        "prototypes": [
            "Nothing in this Agreement shall be construed to create any third-party beneficiary rights.",
        ],
        "keywords": ["third party beneficiary", "no third-party beneficiary", "third-party beneficiary rights"],
    },
}

# --- Practical extension categories (no CUAD gold data; keyword-served) ----
_EXTENSION_LABELS: Dict[str, LabelMeta] = {
    "Indemnification": {
        "name": "Indemnification",
        "kind": "risk",
        "base_risk": "HIGH",
        "prototypes": [
            "The contractor shall indemnify and hold harmless the client from any and all claims, damages, and expenses, including attorney fees.",
            "Party agrees to defend, indemnify, and hold the other party harmless against losses, liabilities, and costs.",
        ],
        "keywords": ["indemnify", "indemnification", "hold harmless", "defend and hold", "attorney fees", "attorneys' fees"],
    },
    "Confidentiality": {
        "name": "Confidentiality",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Each party agrees to keep confidential information secret and not disclose it to third parties without prior written consent.",
            "Recipient shall protect confidential information with the same degree of care as its own proprietary information.",
        ],
        "keywords": ["confidential", "confidentiality", "non-disclosure", "nondisclosure", "proprietary information", "trade secret"],
    },
    "Limitation of Liability": {
        "name": "Limitation of Liability",
        "kind": "risk",
        "base_risk": "HIGH",
        "prototypes": [
            "In no event shall Contractor be liable for indirect, incidental, special, or consequential damages, while Client's liability remains unlimited.",
            "Client shall not be liable under any circumstances for any damages arising from this Agreement.",
        ],
        "keywords": ["no liability", "shall not be liable", "in no event shall", "excludes all liability", "disclaims all liability"],
    },
    "Payment Terms": {
        "name": "Payment Terms",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Client shall pay invoices within thirty days of receipt. Late payments accrue interest at the maximum rate permitted by law.",
            "Payment is due upon completion. Client may withhold payment for disputed amounts.",
        ],
        "keywords": ["payment", "invoice", "fees", "compensation", "net 30", "late fee", "withhold payment"],
    },
    "Dispute Resolution": {
        "name": "Dispute Resolution",
        "kind": "risk",
        "base_risk": "MEDIUM",
        "prototypes": [
            "Any dispute arising out of this agreement shall be resolved by binding arbitration under the rules of the American Arbitration Association.",
        ],
        "keywords": ["arbitration", "dispute resolution", "mediation", "binding arbitration", "class action waiver"],
    },
    "Force Majeure": {
        "name": "Force Majeure",
        "kind": "risk",
        "base_risk": "LOW",
        "prototypes": [
            "Neither party shall be liable for failure to perform due to causes beyond its reasonable control, including acts of god, war, or natural disasters.",
        ],
        "keywords": ["force majeure", "acts of god", "beyond reasonable control", "natural disaster"],
    },
    "General": {
        "name": "General",
        "kind": "risk",
        "base_risk": "LOW",
        "prototypes": [
            "This agreement constitutes the entire agreement between the parties and supersedes all prior negotiations.",
        ],
        "keywords": ["entire agreement", "severability", "waiver", "amendment", "notices under this agreement", "counterparts"],
    },
}

CLAUSE_LABELS: Dict[str, LabelMeta] = {**_CUAD_LABELS, **_EXTENSION_LABELS}

LABEL_NAMES: List[str] = list(CLAUSE_LABELS.keys())

# Labels routed to the Contract Overview panel instead of risk clause cards.
METADATA_LABEL_NAMES: List[str] = [
    name for name, meta in CLAUSE_LABELS.items() if meta["kind"] == "metadata"
]

# Labels shown as scored risk clause cards.
RISK_LABEL_NAMES: List[str] = [
    name for name, meta in CLAUSE_LABELS.items() if meta["kind"] == "risk"
]

# The 41 official CUAD categories only (for fine-tuning label alignment).
CUAD_LABEL_NAMES: List[str] = list(_CUAD_LABELS.keys())

UNKNOWN_LABEL = "Unknown"

DISCLAIMER = (
    "This output is legal information generated by an automated tool, "
    "not professional legal advice. Consult a qualified attorney before "
    "signing or relying on any contract analysis."
)
