import type { AgentStatus } from '../types';

interface Props {
  agentStatus: AgentStatus;
  agentStatusDetail: string;
}

export function AgentStatusBar({ agentStatus, agentStatusDetail }: Props) {
  let label: string;
  let className = 'agent-status-bar';

  switch (agentStatus) {
    case 'thinking':
      label = 'Thinking...';
      className += ' status-thinking';
      break;
    case 'tool_call':
      label = agentStatusDetail ? `Running: ${agentStatusDetail}` : 'Running tool...';
      className += ' status-tool';
      break;
    case 'heartbeat':
      label = agentStatusDetail || 'Heartbeat in progress';
      className += ' status-heartbeat';
      break;
    case 'subagent':
      label = agentStatusDetail
        ? `Background: ${agentStatusDetail}`
        : 'Sub-agent running';
      className += ' status-subagent';
      break;
    default:
      label = 'Idle';
      className += ' status-idle';
      break;
  }

  return (
    <div className={className}>
      <span className="agent-status-label">{label}</span>
    </div>
  );
}
