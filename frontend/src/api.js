import axios from "axios";

const API_BASE = "http://localhost:5001";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

/**
 * Start a scan.
 * @param {string[]} urls   - YouTube URLs
 * @param {number}   interval - Seconds between frames (0.1 – 2.0)
 * @param {number}   threshold - Confidence threshold (0 – 1)
 * @returns {Promise<object>} Scan results
 */
export async function startScan(urls, interval = 0.5, threshold = 0.75) {
  const { data } = await api.post("/api/scan", { urls, interval, threshold });
  return data;
}

/**
 * Retrieve stored results for a job.
 * @param {string} jobId
 */
export async function getResults(jobId) {
  const { data } = await api.get(`/api/results/${jobId}`);
  return data;
}

/**
 * Delete a job and its temp files.
 * @param {string} jobId
 */
export async function deleteJob(jobId) {
  const { data } = await api.delete(`/api/jobs/${jobId}`);
  return data;
}

/**
 * Build a URL to serve a frame image.
 * @param {string} jobId
 * @param {string} filename  - e.g. "frame_00012.jpg"
 */
export function frameUrl(jobId, filename) {
  return `${API_BASE}/api/frames/${jobId}/${filename}`;
}

export default api;
