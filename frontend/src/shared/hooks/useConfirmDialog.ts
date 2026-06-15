import { useState, useCallback } from 'react';

export interface UseConfirmDialogReturn<Entity> {
  isOpen: boolean;
  item: Entity | null;
  open: (item: Entity) => void;
  close: () => void;
}

export function useConfirmDialog<Entity = unknown>(): UseConfirmDialogReturn<Entity> {
  const [isOpen, setIsOpen] = useState(false);
  const [item, setItem] = useState<Entity | null>(null);

  const open = useCallback((targetItem: Entity) => {
    setItem(targetItem);
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    setItem(null);
  }, []);

  return {
    isOpen,
    item,
    open,
    close,
  };
}
