import { useMemo } from "react";

const SEGMENTS = [
  { key: "TWO_WHEELER", label: "2W" },
  { key: "THREE_WHEELER", label: "3W" },
  { key: "FOUR_WHEELER", label: "4W" },
  { key: "TRUCK", label: "Trucks" },
  { key: "BUS", label: "Buses" },
];

function SegmentTabs({ value, onChange, loading = false, error = "" }) {
  const items = useMemo(() => SEGMENTS, []);

  if (error) {
    return <div className="glass-card">Unable to load segments: {error}</div>;
  }

  if (loading) {
    return <div className="skeleton skeleton-tabs" />;
  }

  return (
    <div className="segment-tabs" role="tablist" aria-label="Vehicle segment tabs">
      {items.map((segment) => (
        <button
          key={segment.key}
          type="button"
          role="tab"
          className={`segment-pill ${value === segment.key ? "active" : ""}`}
          onClick={() => onChange?.(segment.key)}
        >
          {segment.label}
        </button>
      ))}
    </div>
  );
}

export default SegmentTabs;
