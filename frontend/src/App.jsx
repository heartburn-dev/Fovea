import { useState } from "react";
import UrlInput from "./components/UrlInput";
import IntervalSlider from "./components/IntervalSlider";
import ScanProgress from "./components/ScanProgress";
import ResultsGallery from "./components/ResultsGallery";
import { startScan } from "./api";
import "./App.css";

function App() {
  const [urls, setUrls] = useState([]);
  const [interval, setInterval_] = useState(0.5);
  const [scanning, setScanning] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleScan = async () => {
    if (urls.length === 0) {
      setError("Enter at least one YouTube URL.");
      return;
    }
    setError(null);
    setResults(null);
    setScanning(true);
    setStatusMsg(
      `Downloading & analyzing ${urls.length} video(s) — this may take a while…`
    );

    try {
      const data = await startScan(urls, interval);
      setResults(data);
    } catch (err) {
      const msg =
        err.response?.data?.error || err.message || "Something went wrong.";
      setError(msg);
    } finally {
      setScanning(false);
      setStatusMsg("");
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🔍 Fovea</h1>
        <p className="subtitle">YouTube Secrets Detection Tool</p>
      </header>

      <main className="app-main">
        <section className="input-section">
          <UrlInput onUrlsChange={setUrls} disabled={scanning} />
          <IntervalSlider
            value={interval}
            onChange={setInterval_}
            disabled={scanning}
          />

          <button
            className="scan-button"
            onClick={handleScan}
            disabled={scanning || urls.length === 0}
          >
            {scanning ? "Scanning…" : "Scan Videos"}
          </button>

          {error && <div className="error-banner">{error}</div>}
        </section>

        {scanning && <ScanProgress message={statusMsg} />}
        {results && <ResultsGallery results={results} />}
      </main>

      <footer className="app-footer">
        <p>Fovea — Secrets Detection for Video Content</p>
      </footer>
    </div>
  );
}

export default App;
