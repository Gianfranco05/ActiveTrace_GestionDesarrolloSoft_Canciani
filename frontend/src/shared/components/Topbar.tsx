import { Button } from '@/shared/components/ui/Button';
import { useAuth } from '@/shared/hooks/useAuth';

interface TopbarProps {
  onMenuToggle: () => void;
}

export function Topbar({ onMenuToggle }: TopbarProps) {
  const { user, logout } = useAuth();

  const avatarLetter = user?.name?.charAt(0)?.toUpperCase() ?? '?';

  return (
    <header className="flex h-16 items-center justify-between border-b border-secondary-200 bg-white px-4 lg:px-6">
      <button
        onClick={onMenuToggle}
        className="rounded-lg p-2 text-secondary-500 hover:bg-secondary-100 lg:hidden"
        aria-label="Abrir menú"
      >
        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </button>

      <div className="hidden lg:block" />

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-600 text-sm font-medium text-white">
            {avatarLetter}
          </div>
          <span className="text-sm font-medium text-secondary-700">
            {user?.name ?? 'Usuario'}
          </span>
        </div>

        <Button variant="ghost" size="sm" onClick={logout}>
          Cerrar sesión
        </Button>
      </div>
    </header>
  );
}
