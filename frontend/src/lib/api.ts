/** The single place that talks to the backend.
 *
 * Two problems this file exists to solve properly.
 *
 * 1. Refresh stampede. If five requests fire at once and all five get a 401,
 *    a naive interceptor sends five refresh calls. Four of them race, and
 *    whichever lands last wins, so the other four have just invalidated the
 *    token they are about to use. Here a single in-flight refresh promise is
 *    shared: the first 401 starts the refresh, everyone else awaits the same
 *    promise, and all of them retry with the one new token.
 *
 * 2. Retry loops. A request is retried at most once. If the retry also comes
 *    back 401, the session is cleared and the failure is surfaced, rather than
 *    bouncing between request and refresh forever.
 *
 * The backend's error envelope is {"error": {"code": ..., "message": ...}},
 * which is unwrapped here so components never dig through response shapes.
 */

import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from "@/lib/tokens";

const BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

/** The last x-request-id the API returned. The system strip displays it, which
 *  makes a failed request traceable straight to a line in the backend log. */
let lastRequestId: string | null = null;
export function getLastRequestId(): string | null {
  return lastRequestId;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

interface ErrorEnvelope {
  error?: { code?: string; message?: string };
}

async function toApiError(response: Response): Promise<ApiError> {
  let code = "http_error";
  let message = `Request failed with status ${response.status}.`;
  try {
    const body: unknown = await response.json();
    const envelope = body as ErrorEnvelope;
    if (envelope.error?.message) {
      code = envelope.error.code ?? code;
      message = envelope.error.message;
    } else if (Array.isArray((body as { detail?: unknown }).detail)) {
      // FastAPI validation errors come back as a list under "detail" and do not
      // use the project envelope, so they are handled separately.
      code = "validation_error";
      message = "Check the highlighted fields and try again.";
    }
  } catch {
    // A non-JSON body (a proxy error page, for instance) leaves the defaults.
  }
  return new ApiError(response.status, code, message);
}

interface TokenPair {
  access_token: string;
  refresh_token: string;
}

/** Shared across concurrent 401s so only one refresh is ever in flight. */
let refreshInFlight: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) throw new ApiError(401, "no_refresh_token", "Session expired.");

  const response = await fetch(`${BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    // The refresh token is spent, revoked or belongs to a deactivated user.
    // There is no recovery from here, so end the session cleanly.
    clearTokens();
    throw await toApiError(response);
  }

  const pair = (await response.json()) as TokenPair;
  setTokens(pair.access_token, pair.refresh_token);
  return pair.access_token;
}

function ensureSingleRefresh(): Promise<string> {
  refreshInFlight ??= refreshAccessToken().finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  /** Set for endpoints that must not carry a token, such as login. */
  anonymous?: boolean;
}

async function send(
  path: string,
  options: RequestOptions,
  token: string | null,
): Promise<Response> {
  const headers: Record<string, string> = {};
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  lastRequestId = response.headers.get("x-request-id") ?? lastRequestId;
  return response;
}

export async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  let response = await send(
    path,
    options,
    options.anonymous ? null : getAccessToken(),
  );

  // One retry, and only for an expired or missing access token.
  if (response.status === 401 && !options.anonymous) {
    const fresh = await ensureSingleRefresh();
    response = await send(path, options, fresh);
    if (response.status === 401) {
      clearTokens();
      throw await toApiError(response);
    }
  }

  if (!response.ok) throw await toApiError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

/** Liveness probe for the system strip. Never throws: the strip reports state,
 *  it does not fail the app. */
export async function ping(): Promise<boolean> {
  try {
    const response = await fetch(`${BASE_URL}/health`);
    lastRequestId = response.headers.get("x-request-id") ?? lastRequestId;
    return response.ok;
  } catch {
    return false;
  }
}
