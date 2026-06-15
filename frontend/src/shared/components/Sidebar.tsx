import { clsx } from 'clsx';
import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

import { useAuth } from '@/shared/hooks/useAuth';
import { NAV_ITEMS } from '@/shared/types/nav';
import pkg from '../../../package.json';

import type { NavItem } from '@/shared/types/nav';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

function NavItemLink({ item, onClose, depth = 0 }: { item: NavItem; onClose: () => void; depth?: number }) {
  const location = useLocation();
  const isActive = location.pathname === item.path ||
    (item.path !== '/dashboard' && location.pathname.startsWith(item.path + '/'));

  return (
    <Link
      to={item.path}
      onClick={onClose}
      className={clsx(
        'flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors',
        isActive
          ? 'bg-primary-50 text-primary-700'
          : 'text-secondary-600 hover:bg-secondary-100 hover:text-secondary-900',
        depth > 0 && 'pl-8'
      )}
    >
      {item.label}
    </Link>
  );
}

function NavGroup({ item, onClose }: { item: NavItem; onClose: () => void }) {
  const location = useLocation();
  const { hasPermission, roles } = useAuth();

  if (
    item.roles &&
    item.roles.length > 0 &&
    !roles.some((r) => item.roles!.includes(r))
  ) {
    return null;
  }

  const visibleChildren = (item.children ?? []).filter(
    (child) => !child.permission || hasPermission(child.permission)
  );

  const isActive = item.children?.some(
    (child) => location.pathname === child.path || location.pathname.startsWith(child.path + '/')
  );

  const [expanded, setExpanded] = useState(isActive);

  if (visibleChildren.length === 0) return null;

  return (
    <li>
      <button
        onClick={() => setExpanded(!expanded)}
        className={clsx(
          'flex w-full items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors',
          isActive
            ? 'bg-primary-50 text-primary-700'
            : 'text-secondary-600 hover:bg-secondary-100 hover:text-secondary-900'
        )}
      >
        <svg
          className={clsx(
            'mr-2 h-3 w-3 transition-transform',
            expanded && 'rotate-90'
          )}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        {item.label}
      </button>
      {expanded && (
        <ul className="mt-1 space-y-1">
          {visibleChildren.map((child) => (
            <li key={child.path}>
              <NavItemLink item={child} onClose={onClose} depth={1} />
            </li>
          ))}
        </ul>
      )}
    </li>
  );
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { hasPermission, roles } = useAuth();

  const visibleItems = NAV_ITEMS.filter((item) => {
    if (item.permission && !hasPermission(item.permission)) return false;
    if (item.roles && item.roles.length > 0 && !roles.some((r) => item.roles!.includes(r))) return false;
    return true;
  });

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={clsx(
          'fixed left-0 top-0 z-30 flex h-full w-64 flex-col bg-white shadow-lg transition-transform duration-200 lg:static lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-16 items-center border-b border-secondary-200 px-6">
          <Link to="/dashboard" className="text-xl font-bold text-primary-600" onClick={onClose}>
            trace
          </Link>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <ul className="space-y-1">
            {visibleItems.map((item) => {
              if (item.children) {
                return <NavGroup key={item.path} item={item} onClose={onClose} />;
              }

              return (
                <li key={item.path}>
                  <NavItemLink item={item} onClose={onClose} />
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="border-t border-secondary-200 px-6 py-4">
          <p className="text-xs text-secondary-400">activia trace v{pkg.version}</p>
        </div>
      </aside>
    </>
  );
}
