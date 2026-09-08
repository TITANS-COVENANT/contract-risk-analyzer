import type { AnalysisResponse, HealthResponse } from "./types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

export function getApiBaseUrl(): string {
  return API_URL;
}

function extractErrorDetail(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== "object") {
    return fallback;
  }

  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        return null;
      })
      .filter(Boolean);
    if (parts.length > 0) {
      return parts.join("; ");
    }
  }

  return fallback;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/api/health`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Health check failed (${response.status})`);
  }
  return (await response.json()) as HealthResponse;
}

export async function analyzeContract(file: File): Promise<AnalysisResponse> {
  const body = new FormData();
  body.append("file", file);

  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/analyze`, {
      method: "POST",
      body,
    });
  } catch {
    throw new Error(
      "Could not reach the analysis API. Check that the backend is running.",
    );
  }

  if (!response.ok) {
    let detail = `Analysis failed (${response.status})`;
    try {
      const payload: unknown = await response.json();
      detail = extractErrorDetail(payload, detail);
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(detail);
  }

  return (await response.json()) as AnalysisResponse;
}
