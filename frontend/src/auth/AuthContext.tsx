/** Session state for the whole app.
 *
 * On boot, if a refresh token is present from a previous visit, the provider
 * calls /auth/me. That single request answers three questions at once: is the
 * stored token still valid, is the account still active, and what is the user's
 * current role. Caching a user object in localStorage instead would let a
 * deactivated or demoted person keep a stale identity in the interface.
 */
import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { request } from "@/lib/api";
import { clearTokens, hasSession, setTokens } from "@/lib/tokens";
import type { TokenPair, User } from "@/types";

export interface AuthState {
  user: User | null;
  /** True until the boot-time session check settles, so routes can wait rather
   *  than bouncing a returning user to the sign-in screen. */
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => void;
}

export const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(hasSession());

  useEffect(() => {
    if (!hasSession()) return;
    let cancelled = false;

    request<User>("/auth/me")
      .then((me) => {
        if (!cancelled) setUser(me);
      })
      .catch(() => {
        // Expired, revoked, or the account was deactivated. Either way there is
        // no session, and the api client has already cleared the tokens.
        if (!cancelled) setUser(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const pair = await request<TokenPair>("/auth/login", {
      method: "POST",
      body: { email, password },
      anonymous: true,
    });
    setTokens(pair.access_token, pair.refresh_token);
    setUser(await request<User>("/auth/me"));
  }, []);

  const signOut = useCallback(() => {
    // Local only for now. Server-side revocation needs a token denylist, which
    // arrives with Redis in a later stage.
    clearTokens();
    setUser(null);
  }, []);

  const value = useMemo<AuthState>(
    () => ({ user, loading, signIn, signOut }),
    [user, loading, signIn, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
