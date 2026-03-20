/**
 * Shows a spinner / status message while a scan is in progress.
 */
export default function ScanProgress({ message }) {
  return (
    <div className="scan-progress">
      <div className="spinner" />
      <p>{message || "Scanning…"}</p>
    </div>
  );
}
