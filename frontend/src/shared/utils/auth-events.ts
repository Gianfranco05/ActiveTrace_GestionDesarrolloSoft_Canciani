type EventListener = (...args: unknown[]) => void;

class AuthEventEmitter {
  private listeners: Map<string, EventListener[]> = new Map();

  on(event: string, listener: EventListener): void {
    const existing = this.listeners.get(event) ?? [];
    existing.push(listener);
    this.listeners.set(event, existing);
  }

  off(event: string, listener: EventListener): void {
    const existing = this.listeners.get(event);
    if (!existing) return;
    this.listeners.set(
      event,
      existing.filter((l) => l !== listener)
    );
  }

  emit(event: string, ...args: unknown[]): void {
    const existing = this.listeners.get(event);
    if (!existing) return;
    for (const listener of existing) {
      listener(...args);
    }
  }
}

export const AuthEvents = new AuthEventEmitter();

export const AUTH_EVENTS = {
  FORCE_LOGOUT: 'force-logout',
} as const;

export function onForceLogout(callback: () => void): () => void {
  AuthEvents.on(AUTH_EVENTS.FORCE_LOGOUT, callback);
  return () => AuthEvents.off(AUTH_EVENTS.FORCE_LOGOUT, callback);
}
