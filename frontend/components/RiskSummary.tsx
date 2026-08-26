"use client";

import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { AnalysisSummary, ClauseResult, RiskLevel } from "@/lib/types";

interface RiskSummaryProps {
  filename: string;
  summary: AnalysisSummary;
  clauses: ClauseResult[];
  onExport?: () => void;
  exporting?: boolean;
}

const RISK_COLOR: Record<RiskLevel, string> = {
  HIGH: "var(--high)",
  MEDIUM: "var(--medium-fg)",
  LOW: "var(--low)",
};

const RISK_RANK: Record<RiskLevel, number> = { LOW: 0, MEDIUM: 1, HIGH: 2 };

interface DonutTooltipPayload {
  name: string;
  value: number;
}

function DonutTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: DonutTooltipPayload }> }) {
  if (!active || !payload?.length) return null;
  const item = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <div className="tt-title">{item.name}</div>
      <div className="tt-row">{item.value} clause{item.value === 1 ? "" : "s"}</div>
    </div>
  );
}

interface BarTooltipPayload {
  category: string;
  count: number;
  dominant: RiskLevel;
}

function BarTooltipContent({ active, payload }: { active?: boolean; payload?: Array<{ payload: BarTooltipPayload }> }) {
  if (!active || !payload?.length) return null;
  const item = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <div className="tt-title">{item.category}</div>
      <div className="tt-row">
        {item.count} clause{item.count === 1 ? "" : "s"} · highest risk {item.dominant}
      </div>
    </div>
  );
}

export default function RiskSummary({
  filename,
  summary,
  clauses,
  onExport,
  exporting = false,
}: RiskSummaryProps) {
  const dominant =
    summary.high > 0 ? "high" : summary.medium > 0 ? "medium" : "low";

  const donutData = useMemo(
    () => [
      { name: "High", value: summary.high, color: RISK_COLOR.HIGH },
      { name: "Medium", value: summary.medium, color: RISK_COLOR.MEDIUM },
      { name: "Low", value: summary.low, color: RISK_COLOR.LOW },
    ],
    [summary],
  );

  const categoryData = useMemo(() => {
    const byCategory = new Map<string, { count: number; dominant: RiskLevel }>();
    for (const clause of clauses) {
      const existing = byCategory.get(clause.category);
      if (!existing) {
        byCategory.set(clause.category, { count: 1, dominant: clause.risk_level });
      } else {
        existing.count += 1;
        if (RISK_RANK[clause.risk_level] > RISK_RANK[existing.dominant]) {
          existing.dominant = clause.risk_level;
        }
      }
    }
    const sorted = Array.from(byCategory.entries())
      .map(([category, v]) => ({ category, count: v.count, dominant: v.dominant }))
      .sort((a, b) => b.count - a.count);

    const TOP_N = 8;
    if (sorted.length <= TOP_N) return sorted;
    const top = sorted.slice(0, TOP_N);
    const rest = sorted.slice(TOP_N);
    const otherCount = rest.reduce((sum, r) => sum + r.count, 0);
    const otherDominant = rest.reduce<RiskLevel>(
      (worst, r) => (RISK_RANK[r.dominant] > RISK_RANK[worst] ? r.dominant : worst),
      "LOW",
    );
    return [...top, { category: `Other (${rest.length})`, count: otherCount, dominant: otherDominant }];
  }, [clauses]);

  return (
    <section className="panel results-panel" aria-label="Risk summary">
      <div className="panel-head">
        <div>
          <h1>Analysis complete</h1>
          <p>
            <span className="file-inline">{filename}</span>
            {" · "}
            {summary.total_clauses} clause
            {summary.total_clauses === 1 ? "" : "s"} reviewed
          </p>
        </div>
        {onExport ? (
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={onExport}
            disabled={exporting}
          >
            {exporting ? "Preparing…" : "Export PDF report"}
          </button>
        ) : null}
      </div>

      <div className={`risk-pulse risk-pulse-${dominant}`}>
        {summary.high > 0
          ? `${summary.high} high-risk clause${summary.high === 1 ? "" : "s"} need attention`
          : summary.medium > 0
            ? "No high-risk clauses — review medium-risk terms carefully"
            : "No high or medium risks detected — still read carefully before signing"}
      </div>

      <div className="summary-grid">
        <div className="stat">
          <div className="label">Clauses</div>
          <div className="value">{summary.total_clauses}</div>
        </div>
        <div className="stat high">
          <div className="label">High risk</div>
          <div className="value">{summary.high}</div>
        </div>
        <div className="stat medium">
          <div className="label">Medium</div>
          <div className="value">{summary.medium}</div>
        </div>
        <div className="stat low">
          <div className="label">Low</div>
          <div className="value">{summary.low}</div>
        </div>
      </div>

      {summary.total_clauses > 0 ? (
        <div className="chart-row" style={{ marginTop: "1rem" }}>
          <div className="chart-card">
            <h3>Risk distribution</h3>
            <p className="chart-sub">Share of clauses by risk level</p>
            <div className="donut-wrap" style={{ height: 168 }}>
              <div style={{ position: "relative", width: 168, height: 168, flexShrink: 0 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={donutData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={54}
                      outerRadius={80}
                      paddingAngle={donutData.filter((d) => d.value > 0).length > 1 ? 3 : 0}
                      stroke="var(--surface)"
                      strokeWidth={2}
                      isAnimationActive={false}
                    >
                      {donutData.map((entry) => (
                        <Cell key={entry.name} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip content={<DonutTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="donut-center">
                  <span className="n">{summary.total_clauses}</span>
                  <span className="l">Clauses</span>
                </div>
              </div>
              <div className="legend-list">
                {donutData.map((entry) => (
                  <div className="legend-row" key={entry.name}>
                    <span className="legend-swatch" style={{ background: entry.color }} />
                    {entry.name}
                    <span className="legend-count">{entry.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="chart-card">
            <h3>Clauses by category</h3>
            <p className="chart-sub">Top categories found, bar color = highest risk seen in that category</p>
            <div style={{ height: 220 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={categoryData}
                  layout="vertical"
                  margin={{ top: 4, right: 16, bottom: 4, left: 4 }}
                  barCategoryGap={8}
                >
                  <CartesianGrid horizontal={false} stroke="var(--border)" />
                  <XAxis
                    type="number"
                    allowDecimals={false}
                    tick={{ fill: "var(--muted)", fontSize: 11 }}
                    axisLine={{ stroke: "var(--border)" }}
                    tickLine={false}
                  />
                  <YAxis
                    type="category"
                    dataKey="category"
                    width={150}
                    tick={{ fill: "var(--ink-soft)", fontSize: 11 }}
                    axisLine={{ stroke: "var(--border)" }}
                    tickLine={false}
                  />
                  <Tooltip content={<BarTooltipContent />} cursor={{ fill: "var(--surface-2)" }} />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={16} isAnimationActive={false}>
                    {categoryData.map((entry) => (
                      <Cell key={entry.category} fill={RISK_COLOR[entry.dominant]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
