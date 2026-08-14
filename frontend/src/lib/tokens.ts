/** Where tokens live, and why.
 *
 * The access token is held in a module variable, never in localStorage. It dies
 * with the tab, which means a cross-site scripting bug cannot read it back out
 * of storage later, and it is the token that actually grants access.
 *
 * The refresh token does go to localStorage, because without it every page
 * reload would force a fresh login. That is a real trade-off, not a free win:
 * an attacker who achieves script execution can read it. The properly hardened
 * answer is an httpOnly, Secure, SameSite cookie set by the backend, which the
 * browser will not hand to JavaScript at all. That needs a backend change
 * (setting and reading cookies in the auth endpoints plus CSRF protection), so
 * it is recorded as a known limitation rather than pretended away.
 *
 * Nothing outside this module touches storage, so switching to cookies later
 * means changing this file and nothing else.
 */

const REFRESH_KEY = "teamflow.refresh_token";

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function getRefreshToken(): string | null {
  try {
    return localStorage.getItem(REFRESH_KEY);
  } catch {
    // Storage can throw in private browsing modes. Treat it as "no token"
    // rather than crashing the whole app on boot.
    return null;
  }
}

export function setTokens(access: string, refresh: string): void {
  accessToken = access;
  try {
    localStorage.setItem(REFRESH_KEY, refresh);
  } catch {
    // Losing persistence degrades the experience to session-only. It does not
    // break the current session, so this is deliberately swallowed.
  }
}

export function clearTokens(): void {
  accessToken = null;
  try {
    localStorage.removeItem(REFRESH_KEY);
  } catch {
    // Nothing useful to do here.
  }
}

export function hasSession(): boolean {
  return accessToken !== null || getRefreshToken() !== null;
}
