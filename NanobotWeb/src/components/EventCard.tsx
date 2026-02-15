import type { AgentEventRecord } from '../types';

interface Props {
  events: AgentEventRecord[];
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatToolChain(events: AgentEventRecord[]): string {
  const tools = events
    .filter(e => e.category === 'agent' && e.event === 'tool_call')
    .map(e => {
      const name = String(e.data.name ?? 'tool');
      const args = e.data.args as Record<string, unknown> | undefined;
      let hint = '';
      if (args) {
        const first = Object.values(args)[0];
        if (typeof first === 'string' && first.length > 0) {
          hint = `("${first.length > 30 ? first.slice(0, 30) + '...' : first}")`;
        }
      }
      return `${name}${hint}`;
    });
  return tools.join(' \u2192 ');
}

interface CardData {
  key: string;
  text: string;
  time: string;
  className: string;
}

export function EventCards({ events }: Props) {
  if (events.length === 0) return null;

  const cards: CardData[] = [];

  // Tool chain — single consolidated card showing the full chain
  const toolEvents = events.filter(e => e.category === 'agent' && e.event === 'tool_call');
  const chain = formatToolChain(events);
  if (chain) {
    const lastTool = toolEvents[toolEvents.length - 1];
    cards.push({
      key: 'tools',
      text: chain,
      time: lastTool ? formatTime(lastTool.timestamp) : '',
      className: 'event-card event-tool',
    });
  }

  // Heartbeat — show only the LATEST tick, not every tick
  const lastHeartbeat = events.findLast(e => e.category === 'heartbeat');
  if (lastHeartbeat) {
    const summary = lastHeartbeat.data.summary
      ? String(lastHeartbeat.data.summary)
      : 'Heartbeat check';
    cards.push({
      key: 'heartbeat',
      text: `Heartbeat \u00b7 ${summary}`,
      time: formatTime(lastHeartbeat.timestamp),
      className: 'event-card event-heartbeat',
    });
  }

  // Subagent — show only the latest event per subagent ID
  const subagentLatest = new Map<string, AgentEventRecord>();
  for (const e of events.filter(e => e.category === 'subagent')) {
    subagentLatest.set(String(e.data.id ?? e.id), e);
  }
  for (const e of subagentLatest.values()) {
    const label = String(e.data.label ?? 'task');
    if (e.event === 'spawned') {
      cards.push({
        key: `sub-${e.id}`,
        text: `Background task: ${label}`,
        time: formatTime(e.timestamp),
        className: 'event-card event-subagent',
      });
    } else if (e.event === 'completed') {
      const ok = e.data.success ? 'completed' : 'failed';
      cards.push({
        key: `sub-${e.id}`,
        text: `Background task: ${label} \u2014 ${ok}`,
        time: formatTime(e.timestamp),
        className: `event-card event-subagent ${e.data.success ? '' : 'event-error'}`,
      });
    }
  }

  // Cron — show only the latest per job name
  const cronLatest = new Map<string, AgentEventRecord>();
  for (const e of events.filter(e => e.category === 'cron')) {
    cronLatest.set(String(e.data.job ?? e.id), e);
  }
  for (const e of cronLatest.values()) {
    const job = String(e.data.job ?? 'job');
    const status = e.data.status === 'ok' ? 'ran successfully' : 'failed';
    cards.push({
      key: `cron-${e.id}`,
      text: `Cron \u00b7 ${job} \u00b7 ${status}`,
      time: formatTime(e.timestamp),
      className: `event-card event-cron ${e.data.status !== 'ok' ? 'event-error' : ''}`,
    });
  }

  if (cards.length === 0) return null;

  return (
    <>
      {cards.map(c => (
        <div key={c.key} className={c.className}>
          <span className="event-card-text">{c.text}</span>
          {c.time && <span className="event-card-time">{c.time}</span>}
        </div>
      ))}
    </>
  );
}
