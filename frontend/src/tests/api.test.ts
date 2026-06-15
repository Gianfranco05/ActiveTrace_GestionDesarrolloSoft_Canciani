import { describe, it, expect, beforeEach, vi } from 'vitest';

import { AuthEvents, AUTH_EVENTS } from '@/shared/utils/auth-events';
import { getAccessToken, setAccessToken, clearAuthTokens, STORAGE_KEYS } from '@/shared/utils/storage';

describe('storage utils', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('stores and retrieves access token', () => {
    setAccessToken('test-token');
    expect(getAccessToken()).toBe('test-token');
  });

  it('clears auth tokens', () => {
    setAccessToken('test-token');
    clearAuthTokens();
    expect(localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)).toBeNull();
  });

  it('returns null when no token exists', () => {
    expect(getAccessToken()).toBeNull();
  });
});

describe('auth-events', () => {
  it('emits and listens to force-logout event', () => {
    const listener = vi.fn();

    AuthEvents.on(AUTH_EVENTS.FORCE_LOGOUT, listener);
    AuthEvents.emit(AUTH_EVENTS.FORCE_LOGOUT);

    expect(listener).toHaveBeenCalledTimes(1);
  });

  it('unsubscribes from events', () => {
    const listener = vi.fn();

    AuthEvents.on(AUTH_EVENTS.FORCE_LOGOUT, listener);
    AuthEvents.off(AUTH_EVENTS.FORCE_LOGOUT, listener);
    AuthEvents.emit(AUTH_EVENTS.FORCE_LOGOUT);

    expect(listener).not.toHaveBeenCalled();
  });
});
