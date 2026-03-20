/**
 * Slider to choose the frame extraction interval (seconds between frames).
 */
export default function IntervalSlider({ value, onChange, disabled }) {
  return (
    <div className="interval-slider">
      <label htmlFor="interval-range">
        Frame interval: <strong>{value.toFixed(1)}s</strong>
      </label>
      <input
        id="interval-range"
        type="range"
        min={0.1}
        max={2.0}
        step={0.1}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        disabled={disabled}
      />
      <div className="interval-slider__labels">
        <span>0.1s (more frames)</span>
        <span>2.0s (fewer frames)</span>
      </div>
    </div>
  );
}
