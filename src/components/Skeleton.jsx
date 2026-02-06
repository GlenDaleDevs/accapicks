import "./Skeleton.css";

export default function Skeleton({ width = "100%", height = "16px", count = 1 }) {
  return (
    <div className="skeleton-wrapper">
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className="skeleton-bar"
          style={{ width, height }}
        />
      ))}
    </div>
  );
}
