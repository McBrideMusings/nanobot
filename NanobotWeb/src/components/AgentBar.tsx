import type { AgentStatus } from '../types';
import type { ConnectionStatus } from '../hooks/useWebSocket';
import { BotIcon, ChevronDownIcon, ServerIcon, GearIcon } from './Icons';

interface Props {
  agentStatus: AgentStatus;
  agentStatusDetail: string;
  connectionStatus: ConnectionStatus;
  onOpenProfile: () => void;
  onOpenConnection: () => void;
  onOpenSettings: () => void;
}

function getStatusText(
  agentStatus: AgentStatus,
  agentStatusDetail: string,
  connectionStatus: ConnectionStatus,
): { text: string; className: string } {
  switch (agentStatus) {
    case 'thinking':
      return { text: 'Thinking...', className: 'agent-bar-status status-thinking' };
    case 'tool_call':
      return {
        text: agentStatusDetail ? `Running: ${agentStatusDetail}` : 'Running tool...',
        className: 'agent-bar-status status-tool',
      };
    case 'heartbeat':
      return {
        text: agentStatusDetail || 'Heartbeat',
        className: 'agent-bar-status status-heartbeat',
      };
    case 'subagent':
      return {
        text: agentStatusDetail ? `Background: ${agentStatusDetail}` : 'Sub-agent running',
        className: 'agent-bar-status status-subagent',
      };
    default:
      return {
        text: connectionStatus === 'connected' ? 'Online' : 'Offline',
        className: `agent-bar-status status-idle${connectionStatus !== 'connected' ? ' offline' : ''}`,
      };
  }
}

function getConnDotClass(connectionStatus: ConnectionStatus): string {
  switch (connectionStatus) {
    case 'connected': return 'conn-dot connected';
    case 'connecting': return 'conn-dot connecting';
    default: return 'conn-dot disconnected';
  }
}

export function AgentBar({
  agentStatus,
  agentStatusDetail,
  connectionStatus,
  onOpenProfile,
  onOpenConnection,
  onOpenSettings,
}: Props) {
  const { text, className } = getStatusText(agentStatus, agentStatusDetail, connectionStatus);

  return (
    <div className="agent-bar">
      <button className="agent-bar-left" onClick={onOpenProfile}>
        <BotIcon size={18} />
        <span className="agent-bar-name">Nanobot</span>
        <ChevronDownIcon size={14} />
      </button>
      <span className={className}>{text}</span>
      <div className="agent-bar-right">
        <button className="agent-bar-icon-btn" onClick={onOpenConnection} title="Connection">
          <ServerIcon size={16} />
          <span className={getConnDotClass(connectionStatus)} />
        </button>
        <button className="agent-bar-icon-btn" onClick={onOpenSettings} title="Settings">
          <GearIcon size={16} />
        </button>
      </div>
    </div>
  );
}
