import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { FileUpload } from '@/shared/components/ui/FileUpload';

describe('FileUpload', () => {
  it('renders button with default label', () => {
    const onFileSelect = vi.fn();
    render(<FileUpload onFileSelect={onFileSelect} />);

    expect(screen.getByText('Seleccionar archivo')).toBeInTheDocument();
  });

  it('shows file name after selection', () => {
    const onFileSelect = vi.fn();
    render(<FileUpload onFileSelect={onFileSelect} />);

    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByRole('button').previousElementSibling as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByText('test.csv')).toBeInTheDocument();
  });

  it('calls onFileSelect with the file', () => {
    const onFileSelect = vi.fn();
    render(<FileUpload onFileSelect={onFileSelect} />);

    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByRole('button').previousElementSibling as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    expect(onFileSelect).toHaveBeenCalledWith(file);
  });

  it('shows error for oversized file', () => {
    const onFileSelect = vi.fn();
    render(<FileUpload onFileSelect={onFileSelect} maxSizeMB={0.001} />);

    const file = new File(['x'.repeat(2000)], 'test.csv', { type: 'text/csv' });
    const input = screen.getByRole('button').previousElementSibling as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    expect(onFileSelect).not.toHaveBeenCalled();
    expect(screen.getByText(/tamaño máximo/i)).toBeInTheDocument();
  });

  it('shows drag-drop UI when onUpload is provided', () => {
    const onUpload = vi.fn();
    render(<FileUpload onUpload={onUpload} />);

    expect(screen.getByText(/arrastrá el archivo/i)).toBeInTheDocument();
  });

  it('shows progress bar when uploading with advanced mode', () => {
    const onUpload = vi.fn();
    render(<FileUpload onUpload={onUpload} uploading progress={45} />);

    expect(screen.getByText('45%')).toBeInTheDocument();
    expect(screen.getByText('Subiendo archivo...')).toBeInTheDocument();
  });
});
