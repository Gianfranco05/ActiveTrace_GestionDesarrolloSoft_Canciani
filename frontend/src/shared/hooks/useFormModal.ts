import { useState, useCallback } from 'react';

export interface UseFormModalReturn<FormData, Entity> {
  isOpen: boolean;
  selectedItem: Entity | null;
  formData: FormData;
  openCreate: (initialData?: Partial<FormData>) => void;
  openEdit: (item: Entity, initialData: FormData) => void;
  close: () => void;
  setFormData: React.Dispatch<React.SetStateAction<FormData>>;
}

export function useFormModal<FormData, Entity = unknown>(
  defaultFormData: FormData
): UseFormModalReturn<FormData, Entity> {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<Entity | null>(null);
  const [formData, setFormData] = useState<FormData>(defaultFormData);

  const openCreate = useCallback(
    (initialData?: Partial<FormData>) => {
      setSelectedItem(null);
      setFormData({ ...defaultFormData, ...initialData });
      setIsOpen(true);
    },
    [defaultFormData]
  );

  const openEdit = useCallback((item: Entity, initialData: FormData) => {
    setSelectedItem(item);
    setFormData(initialData);
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    setSelectedItem(null);
    setFormData(defaultFormData);
  }, [defaultFormData]);

  return {
    isOpen,
    selectedItem,
    formData,
    openCreate,
    openEdit,
    close,
    setFormData,
  };
}
