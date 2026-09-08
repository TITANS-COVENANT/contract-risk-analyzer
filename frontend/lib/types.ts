export type RiskLevel = "HIGH" | "MEDIUM" | "LOW";

export interface ClauseResult {
  id: number;
  category: string;
  confidence: number;
  risk_level: RiskLevel;
  risk_reasons: string[];
  original_text: string;
  plain_english: string;
  suggested_alternative: string;
  llm_available: boolean;
}

export interface AnalysisSummary {
  total_clauses: number;
  high: number;
  medium: number;
  low: number;
}

export interface DocumentMetadata {
  document_name: string | null;
  parties: string | null;
  agreement_date: string | null;
  effective_date: string | null;
  expiration_date: string | null;
  governing_law: string | null;
}

export interface AnalysisResponse {
  filename: string;
  disclaimer: string;
  summary: AnalysisSummary;
  document_metadata: DocumentMetadata;
  clauses: ClauseResult[];
  processing_notes: string[];
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  fine_tuned: boolean;
  classifier_labels: number;
  llm_configured: boolean;
  llm_provider: string;
  version: string;
}
