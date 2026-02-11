import type { ConnectionStatus as Status } from '../hooks/useWebSocket';

interface Props {
  status: Status;
}

const STATUS_LABELS: Record<Status, string> = {
  connected: 'Connected',
  disconnected: 'Disconnected',
  connecting: 'Connecting...',
};

export function ConnectionStatus({ status }: Props) {
  return (
    <span className={`connection-status ${status}`}>
      <span className="status-dot" />
      {STATUS_LABELS[status]}
    </span>
  );
}
