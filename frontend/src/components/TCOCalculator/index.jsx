import { useMemo, useState } from "react";
import { vehicleAPI } from "../../services/api";

function TCOCalculator({ vehicleId }) {
  const [dailyKm, setDailyKm] = useState(30);
  const [state, setState] = useState("karnataka");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const currency = useMemo(
    () => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }),
    []
  );

  const run = async () => {
    if (!vehicleId) return;
    setLoading(true);
    setError("");
    try {
      const res = await vehicleAPI.getSubsidies({ vehicle_id: vehicleId, state, daily_km: dailyKm });
      setResult(res.data);
    } catch (e) {
      setError(e?.response?.data?.detail || "Could not calculate TCO");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card">
      <h3>5-Year TCO Calculator</h3>
      <div className="filter-bar" style={{ marginTop: 12 }}>
        <input className="input" type="number" min={1} value={dailyKm} onChange={(e) => setDailyKm(Number(e.target.value))} />
        <input className="input" value={state} onChange={(e) => setState(e.target.value)} />
        <button type="button" className="btn btn-primary" onClick={run} disabled={loading}>
          {loading ? "Calculating..." : "Calculate"}
        </button>
      </div>
      {loading && <div className="skeleton" style={{ height: 80, marginTop: 12 }} />}
      {error && <p style={{ color: "var(--text-muted)", marginTop: 12 }}>{error}</p>}
      {result && (
        <div style={{ marginTop: 12 }}>
          <p>Total Subsidies: {currency.format(result.total_applicable_subsidies || 0)}</p>
          <p><strong>TCO 5Y:</strong> {currency.format(result.tco_5year_inr || 0)}</p>
        </div>
      )}
    </div>
  );
}

export default TCOCalculator;
