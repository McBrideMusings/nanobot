import type { NavTab } from '../types';
import { ChatIcon, CanvasIcon, FilesIcon, TerminalIcon } from './Icons';

const NAV_TABS: { id: NavTab; label: string; icon: React.ComponentType<{ size?: number }> }[] = [
  { id: 'chat', label: 'Chat', icon: ChatIcon },
  { id: 'canvas', label: 'Canvas', icon: CanvasIcon },
  { id: 'files', label: 'Files', icon: FilesIcon },
  { id: 'logs', label: 'Logs', icon: TerminalIcon },
];

interface Props {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
}

export function TabBar({ activeTab, onTabChange }: Props) {
  return (
    <div className="tab-bar">
      {NAV_TABS.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          className={`tab-btn${activeTab === id ? ' active' : ''}`}
          onClick={() => onTabChange(id)}
        >
          <Icon size={20} />
          <span>{label}</span>
        </button>
      ))}
    </div>
  );
}
