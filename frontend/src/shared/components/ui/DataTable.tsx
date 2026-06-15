import { clsx } from 'clsx';
import { useState, useMemo, type ReactNode } from 'react';

export interface Column {
  key: string;
  header: ReactNode;
  sortable?: boolean;
  render?: (item: any) => ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column[];
  data: T[];
  keyExtractor: (item: T, index: number) => string;
  pageSize?: number;
  emptyMessage?: string;
  isLoading?: boolean;
  actions?: ReactNode;
  onRowClick?: (item: T) => void;
}

/**
 * Generic data table with sorting and pagination.
 * 
 * T is inferred from the `data` prop. Columns accept any data shape via `render` callbacks.
 * Use `(item: YourType)` in render callbacks for type-safe access within the function.
 * 
 * Example:
 * ```tsx
 * const cols: Column[] = [
 *   { key: 'name', header: 'Name' },
 *   { key: 'actions', header: '', render: (item: User) => <Button /> },
 * ];
 * <DataTable columns={cols} data={users} keyExtractor={u => u.id} />
 * ```
 */
export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  pageSize = 0,
  emptyMessage = 'No hay datos disponibles',
  isLoading = false,
  actions,
  onRowClick,
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState(0);

  const sorted = useMemo(() => {
    if (!sortKey) return data;
    return [...data].sort((a, b) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const aVal = (a as any)[sortKey];
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const bVal = (b as any)[sortKey];
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;
      const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [data, sortKey, sortDir]);

  const totalPages = pageSize > 0 ? Math.max(1, Math.ceil(sorted.length / pageSize)) : 1;
  const paginated = pageSize > 0 ? sorted.slice(page * pageSize, (page + 1) * pageSize) : sorted;

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-600 border-t-transparent" />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center py-8">
        <p className="text-sm text-secondary-500">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div>
      {actions && <div className="mb-4">{actions}</div>}
      <div className="overflow-x-auto rounded-lg border border-secondary-200">
        <table className="min-w-full divide-y divide-secondary-200">
          <thead className="bg-secondary-50">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={clsx(
                    'px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-secondary-500',
                    col.sortable && 'cursor-pointer select-none hover:text-secondary-900',
                    col.className
                  )}
                  onClick={() => col.sortable && handleSort(col.key)}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.header}
                    {col.sortable && sortKey === col.key && (
                      <span>{sortDir === 'asc' ? '\u25B2' : '\u25BC'}</span>
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-secondary-200 bg-white">
            {paginated.map((item, idx) => (
              <tr
                key={keyExtractor(item, idx)}
                className={clsx('hover:bg-secondary-50', onRowClick && 'cursor-pointer')}
                onClick={() => onRowClick?.(item)}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={clsx('whitespace-nowrap px-4 py-3 text-sm text-secondary-700', col.className)}
                  >
                    {col.render ? col.render(item as any) : (item as any)[col.key] as ReactNode}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-between">
          <span className="text-sm text-secondary-500">
            Página {page + 1} de {totalPages} ({sorted.length} registros)
          </span>
          <div className="flex gap-1">
            <button
              className="rounded px-3 py-1 text-sm text-secondary-600 hover:bg-secondary-100 disabled:text-secondary-300 disabled:cursor-not-allowed"
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              Anterior
            </button>
            <button
              className="rounded px-3 py-1 text-sm text-secondary-600 hover:bg-secondary-100 disabled:text-secondary-300 disabled:cursor-not-allowed"
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
