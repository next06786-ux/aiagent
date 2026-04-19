import type { TimelineEvent } from '../../types/api';

interface TimelineMapProps {
  events: TimelineEvent[];
  accent: string;
  selectedEventId?: string;
  onSelect?: (event: TimelineEvent) => void;
}

interface PositionedEvent {
  key: string;
  event: TimelineEvent;
  x: number;
  y: number;
}

function fallbackId(event: TimelineEvent, index: number) {
  return event.event_id || `event_${event.month}_${index}`;
}

export function TimelineMap({
  events,
  accent,
  selectedEventId,
  onSelect,
}: TimelineMapProps) {
  const ordered = [...events].sort((left, right) => {
    if (left.month !== right.month) {
      return left.month - right.month;
    }
    return (left.node_level || 0) - (right.node_level || 0);
  });

  const mainEvents = ordered.filter(
    (event) => !String(event.branch_group || '').endsWith('_fork'),
  );
  const positioned: PositionedEvent[] = [];
  const positions = new Map<string, PositionedEvent>();

  mainEvents.forEach((event, index) => {
    const key = fallbackId(event, index);
    const item = {
      key,
      event,
      x: 120 + Math.max(index, event.month - 1) * 110,
      y: 210,
    };
    positioned.push(item);
    positions.set(key, item);
  });

  ordered
    .filter((event) => String(event.branch_group || '').endsWith('_fork'))
    .forEach((event, index) => {
      const key = fallbackId(event, index + mainEvents.length);
      const parent = event.parent_event_id
        ? positions.get(event.parent_event_id)
        : positioned[positioned.length - 1];
      const branchOffset =
        event.risk_tag === 'high'
          ? 92
          : event.risk_tag === 'low'
            ? -92
            : index % 2 === 0
              ? 64
              : -64;
      const item = {
        key,
        event,
        x: (parent?.x || 120) + 128,
        y: (parent?.y || 210) + branchOffset,
      };
      positioned.push(item);
      positions.set(key, item);
    });

  const maxX = Math.max(...positioned.map((item) => item.x), 540) + 120;
  const guideLines = Array.from({ length: Math.max(6, Math.ceil(maxX / 120)) });

  return (
    <div className="timeline-map">
      <svg
        viewBox={`0 0 ${maxX} 420`}
        preserveAspectRatio="xMidYMid meet"
        className="timeline-svg"
      >
        <defs>
          <linearGradient id="timelineAccent" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={accent} stopOpacity="0.95" />
            <stop offset="100%" stopColor="#ffffff" stopOpacity="0.9" />
          </linearGradient>
        </defs>

        {guideLines.map((_, index) => (
          <g key={`guide_${index}`}>
            <line
              x1={80 + index * 120}
              y1="48"
              x2={80 + index * 120}
              y2="368"
              className="timeline-guide"
            />
            <text x={72 + index * 120} y="394" className="timeline-month">
              {index + 1}M
            </text>
          </g>
        ))}

        <line x1="48" y1="210" x2={maxX - 48} y2="210" className="timeline-axis" />
        <circle cx="64" cy="210" r="12" className="timeline-origin" />
        <text x="44" y="184" className="timeline-origin-label">
          Start
        </text>

        {positioned.map((item, index) => {
          const parentKey = item.event.parent_event_id || '';
          const parent = positions.get(parentKey);
          const fromX = parent ? parent.x : 64;
          const fromY = parent ? parent.y : 210;
          return (
            <path
              key={`line_${item.key}_${index}`}
              d={`M ${fromX} ${fromY} C ${fromX + 40} ${fromY}, ${item.x - 40} ${item.y}, ${item.x} ${item.y}`}
              className="timeline-line"
            />
          );
        })}

        {positioned.map((item) => {
          const isSelected =
            selectedEventId === item.key || selectedEventId === item.event.event_id;
          const score =
            Object.values(item.event.impact || {}).reduce((sum, value) => sum + value, 0) *
            100;
          return (
            <g
              key={item.key}
              className="timeline-node"
              onClick={() => onSelect?.(item.event)}
            >
              <circle
                cx={item.x}
                cy={item.y}
                r={isSelected ? 20 : 16}
                fill="url(#timelineAccent)"
                className={isSelected ? 'timeline-node-active' : ''}
              />
              <circle
                cx={item.x}
                cy={item.y}
                r={isSelected ? 10 : 8}
                className="timeline-node-core"
              />
              <text x={item.x - 24} y={item.y - 28} className="timeline-probability">
                可行性 {(item.event.probability * 100).toFixed(0)}
              </text>
              <foreignObject
                x={item.x - 70}
                y={item.y + 24}
                width="140"
                height="100"
                className="timeline-label-box"
              >
                <div className="timeline-label">
                  <strong>{item.event.event}</strong>
                  <span>净影响 {score.toFixed(0)}</span>
                </div>
              </foreignObject>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
