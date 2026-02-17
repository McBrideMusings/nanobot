import type { NavTab } from '../types';
import { ChatIcon, CanvasIcon, FilesIcon, TasksIcon, TerminalIcon } from './Icons';

const NAV_TABS: { id: NavTab; label: string; icon: React.ComponentType<{ size?: number }> }[] = [
  { id: 'chat', label: 'Chat', icon: ChatIcon },
  { id: 'canvas', label: 'Canvas', icon: CanvasIcon },
  { id: 'files', label: 'Files', icon: FilesIcon },
  { id: 'tasks', label: 'Tasks', icon: TasksIcon },
  { id: 'logs', label: 'Logs', icon: TerminalIcon },
];

interface Props {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
}

export function ActivityBar({ activeTab, onTabChange }: Props) {
  return (
    <nav className="activity-bar">
      {NAV_TABS.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          className={`activity-bar-btn${activeTab === id ? ' active' : ''}`}
          onClick={() => onTabChange(id)}
          title={label}
        >
          <Icon size={20} />
        </button>
      ))}
    </nav>
  );
}
