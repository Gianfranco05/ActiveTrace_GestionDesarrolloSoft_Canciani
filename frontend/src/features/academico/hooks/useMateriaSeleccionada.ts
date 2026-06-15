import { useSearchParams } from 'react-router-dom';

export function useMateriaSeleccionada(): [string, (id: string) => void] {
  const [searchParams, setSearchParams] = useSearchParams();
  const materiaId = searchParams.get('materiaId') ?? '';

  const setMateriaId = (id: string) => {
    setSearchParams((prev) => {
      if (id) {
        prev.set('materiaId', id);
      } else {
        prev.delete('materiaId');
      }
      return prev;
    }, { replace: true });
  };

  return [materiaId, setMateriaId];
}
