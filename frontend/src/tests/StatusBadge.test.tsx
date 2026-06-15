import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { StatusBadge } from '@/shared/components/ui/StatusBadge';

describe('StatusBadge', () => {
  it('renders Pendiente with amber colors', () => {
    render(<StatusBadge status="Pendiente" />);
    const badge = screen.getByText('Pendiente');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('amber');
  });

  it('renders Enviado with green colors', () => {
    render(<StatusBadge status="Enviado" />);
    const badge = screen.getByText('Enviado');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('green');
  });

  it('renders Error with red colors', () => {
    render(<StatusBadge status="Error" />);
    const badge = screen.getByText('Error');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('red');
  });

  it('renders Cancelado with gray colors', () => {
    render(<StatusBadge status="Cancelado" />);
    const badge = screen.getByText('Cancelado');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('gray');
  });

  it('renders Enviando with blue colors', () => {
    render(<StatusBadge status="Enviando" />);
    const badge = screen.getByText('Enviando');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('blue');
  });

  it('renders unknown status with default gray', () => {
    render(<StatusBadge status="Desconocido" />);
    const badge = screen.getByText('Desconocido');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('gray');
  });
});
