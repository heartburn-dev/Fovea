import { useState, useCallback } from "react";

/**
 * URL input component.
 * Supports pasting URLs (one per line) or uploading a .txt/.csv file.
 */
export default function UrlInput({ onUrlsChange, disabled }) {
  const [text, setText] = useState("");

  const handleTextChange = (e) => {
    setText(e.target.value);
    const urls = parseUrls(e.target.value);
    onUrlsChange(urls);
  };

  const handleFileUpload = useCallback(
    (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (ev) => {
        const content = ev.target.result;
        setText(content);
        onUrlsChange(parseUrls(content));
      };
      reader.readAsText(file);
    },
    [onUrlsChange]
  );

  return (
    <div className="url-input">
      <label htmlFor="url-textarea">YouTube URL(s)</label>
      <textarea
        id="url-textarea"
        rows={4}
        placeholder={"Paste one or more YouTube URLs, one per line…\nhttps://youtube.com/watch?v=..."}
        value={text}
        onChange={handleTextChange}
        disabled={disabled}
      />
      <div className="url-input__actions">
        <label className="file-upload-label" htmlFor="url-file">
          Or upload a .txt / .csv file
        </label>
        <input
          id="url-file"
          type="file"
          accept=".txt,.csv"
          onChange={handleFileUpload}
          disabled={disabled}
        />
      </div>
    </div>
  );
}

function parseUrls(text) {
  return text
    .split(/[\n,]+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0 && s.startsWith("http"));
}
