function RangeBar({ label, ciLow, ciHigh, observed, mean, domainMin, domainMax, threshold, fmt, probLabel }) {
  const pct = (v) => ((v - domainMin) / (domainMax - domainMin)) * 100;
  const belowThreshold = threshold != null && ciLow < threshold;

  return (
    <div style={{ marginBottom: 22 }}>
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: 4, fontSize: 12, marginBottom: 6 }}>
        <span style={{ color: "var(--text-dim)" }}>{label}</span>
        <span className="mono" style={{ color: "var(--text)", whiteSpace: "nowrap" }}>
          {fmt(observed)} <span style={{ color: "var(--text-faint)" }}>obs</span>
          {"  "}·{"  "}
          <span style={{ color: "var(--text-faint)" }}>CI [{fmt(ciLow)}, {fmt(ciHigh)}]</span>
        </span>
      </div>
      <div style={{ position: "relative", height: 10, background: "var(--panel-2)", borderRadius: 5 }}>
        <div
          style={{
            position: "absolute", top: 0, bottom: 0,
            left: `${Math.max(0, pct(ciLow))}%`,
            width: `${Math.min(100, pct(ciHigh)) - Math.max(0, pct(ciLow))}%`,
            background: belowThreshold ? "var(--warn)" : "var(--good)",
            opacity: 0.35, borderRadius: 5,
          }}
        />
        {threshold != null && (
          <div style={{ position: "absolute", left: `${pct(threshold)}%`, top: -3, bottom: -3, width: 2, background: "var(--text-faint)" }} />
        )}
        <div
          style={{
            position: "absolute", left: `${pct(observed)}%`, top: -3, width: 3, height: 16,
            background: "var(--text)", borderRadius: 2, transform: "translateX(-1.5px)",
          }}
        />
      </div>
      {probLabel && (
        <div style={{ fontSize: 11, color: "var(--text-faint)", marginTop: 5 }}>{probLabel}</div>
      )}
    </div>
  );
}

export default function BootstrapPanel({ bootstrap, ddPermutation }) {
  const pf = bootstrap["Profit Factor"];
  const wr = bootstrap["Win Rate (%)"];
  const exp = bootstrap["Expectancy"];

  return (
    <div className="two-col">
      <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: 16 }}>
        <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 14 }}>
          Bootstrap 95% CI &middot; resample return bulanan
        </div>
        <RangeBar
          label="Profit Factor"
          observed={pf.observed} ciLow={pf.ci_low} ciHigh={pf.ci_high}
          domainMin={0} domainMax={Math.max(4.5, pf.ci_high)} threshold={1}
          fmt={(v) => v.toFixed(2)}
          probLabel={`P(PF>1) = ${(pf.prob_above * 100).toFixed(1)}% — garis vertikal = ambang breakeven`}
        />
        <RangeBar
          label="Win Rate"
          observed={wr.observed} ciLow={wr.ci_low} ciHigh={wr.ci_high}
          domainMin={0} domainMax={100} threshold={null}
          fmt={(v) => `${v.toFixed(0)}%`}
        />
        <RangeBar
          label="Return rata-rata / bulan"
          observed={exp.observed} ciLow={exp.ci_low} ciHigh={exp.ci_high}
          domainMin={Math.min(exp.ci_low, 0) * 1.15} domainMax={exp.ci_high * 1.15} threshold={0}
          fmt={(v) => `${v > 0 ? "+" : ""}${v.toFixed(2)}%`}
          probLabel={`P(>0) = ${(exp.prob_above * 100).toFixed(1)}%`}
        />
      </div>

      <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: 16 }}>
        <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 14 }}>
          Max drawdown &middot; permutasi urutan bulan, 20.000 iterasi
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(90px, 1fr))", gap: 10 }}>
          {[
            ["Teramati", ddPermutation.observed, "var(--text)"],
            ["Median", ddPermutation.median, "var(--text-dim)"],
            ["p75", ddPermutation.p75, "var(--text-dim)"],
            ["p95 (perencanaan)", ddPermutation.p95, "var(--warn)"],
            ["p99", ddPermutation.p99, "var(--bad)"],
            ["Maks", ddPermutation.max, "var(--bad)"],
          ].map(([lbl, val, color]) => (
            <div key={lbl} style={{ background: "var(--panel-2)", borderRadius: 8, padding: "10px 10px" }}>
              <div style={{ fontSize: 11, color: "var(--text-faint)", marginBottom: 4 }}>{lbl}</div>
              <div className="mono" style={{ fontSize: 17, fontWeight: 600, color }}>{val.toFixed(1)}%</div>
            </div>
          ))}
        </div>
        <div style={{ fontSize: 11, color: "var(--text-faint)", marginTop: 12 }}>
          {ddPermutation.pct_worse_than_observed.toFixed(0)}% dari urutan acak menghasilkan DD lebih buruk
          dari yang teramati di backtest — urutan trade sebenarnya cukup tipikal, bukan kebetulan bagus.
        </div>
      </div>
    </div>
  );
}
