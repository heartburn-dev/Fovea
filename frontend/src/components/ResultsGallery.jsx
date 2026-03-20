import { useState } from "react";
import { frameUrl } from "../api";

/**
 * Displays scan results.
 * - "All Clear" banner when nothing is flagged
 * - Clickable thumbnail grid for flagged frames
 * - Modal lightbox to enlarge a frame
 */
export default function ResultsGallery({ results }) {
  const [lightbox, setLightbox] = useState(null);

  if (!results) return null;

  const { job_id, videos, summary } = results;

  // Collect all flagged frames across all videos
  const allFlagged = videos.flatMap((v) =>
    (v.frames || []).map((f) => ({ ...f, videoUrl: v.url }))
  );

  const errorVideos = videos.filter((v) => v.status === "error");
  const hasErrors = errorVideos.length > 0;
  const allFailed = errorVideos.length === videos.length;

  return (
    <div className="results-gallery">
      {/* Per-video errors — shown first */}
      {errorVideos.map((v, i) => (
        <div key={i} className="video-error">
          <strong>Error:</strong> {v.url} — {v.error}
        </div>
      ))}

      {/* Summary banner — only shown when at least one video succeeded */}
      {!allFailed && (
        <div className={`results-banner ${summary.total_flagged === 0 ? "clear" : "warning"}`}>
          {summary.total_flagged === 0 ? (
            <>
              <span className="icon">✅</span>
              <span>
                All clear — scanned <strong>{summary.total_frames}</strong> frames
                {hasErrors
                  ? ` across ${summary.total_videos - errorVideos.length} of ${summary.total_videos} video(s)`
                  : ` across ${summary.total_videos} video(s)`
                }. No secrets detected.
              </span>
            </>
          ) : (
            <>
              <span className="icon">⚠️</span>
              <span>
                Found <strong>{summary.total_flagged}</strong> potentially sensitive frame(s) out of{" "}
                <strong>{summary.total_frames}</strong> total.
              </span>
            </>
          )}
        </div>
      )}

      {/* Flagged frames grid */}
      {allFlagged.length > 0 && (
        <div className="frames-grid">
          {allFlagged.map((frame, idx) => (
            <div
              key={idx}
              className="frame-card"
              onClick={() => setLightbox(frame)}
            >
              <img
                src={frameUrl(job_id, frame.filename)}
                alt={`Frame at ${frame.timestamp}s`}
                loading="lazy"
              />
              <div className="frame-card__meta">
                <span className="timestamp">{frame.timestamp}s</span>
                <span className="confidence">
                  {(frame.confidence * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Lightbox modal */}
      {lightbox && (
        <div className="lightbox-overlay" onClick={() => setLightbox(null)}>
          <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
            <button className="lightbox-close" onClick={() => setLightbox(null)}>
              ✕
            </button>
            <img
              src={frameUrl(job_id, lightbox.filename)}
              alt={`Frame at ${lightbox.timestamp}s`}
            />
            <div className="lightbox-meta">
              <p>Timestamp: {lightbox.timestamp}s</p>
              <p>Confidence: {(lightbox.confidence * 100).toFixed(1)}%</p>
              <p>Label: {lightbox.label}</p>
              <p className="lightbox-url">{lightbox.videoUrl}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
