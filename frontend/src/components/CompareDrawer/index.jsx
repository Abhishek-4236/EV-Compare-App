function CompareDrawer({ selected = [], loading = false, error = "" }) {
  if (error) {
    return <div className="compare-drawer">Compare unavailable: {error}</div>;
  }

  if (loading) {
    return <div className="compare-drawer skeleton" style={{ height: 64 }} />;
  }

  if (selected.length < 2) return null;

  return (
    <div className="compare-drawer">
      <span>{selected.length} vehicles selected</span>
      <a className="btn btn-primary" href={`/compare?ids=${selected.join(",")}`}>
        Compare Now
      </a>
    </div>
  );
}

export default CompareDrawer;
