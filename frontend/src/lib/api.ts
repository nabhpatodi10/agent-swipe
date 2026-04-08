import { clearAccessToken, getAccessToken, setAccessToken } from "./auth";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.toString() || "http://localhost:8000";

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  auth?: "user" | "agent" | "none";
  agentToken?: string;
};

async function parseResponse(response: Response): Promise<unknown> {
  const isJson = response.headers.get("content-type")?.includes("application/json");
  if (response.status === 204) return null;
  return isJson ? response.json() : response.text();
}

async function refreshAccessToken(): Promise<string | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (!response.ok) return null;
    const data = (await response.json()) as { access_token?: string };
    if (!data.access_token) return null;
    setAccessToken(data.access_token);
    return data.access_token;
  } catch {
    return null;
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, auth = "user", agentToken, headers, ...rest } = options;
  const requestHeaders = new Headers(headers);

  if (body !== undefined && !requestHeaders.has("Content-Type")) {
    requestHeaders.set("Content-Type", "application/json");
  }

  if (auth === "user") {
    const token = getAccessToken();
    if (token) requestHeaders.set("Authorization", `Bearer ${token}`);
  } else if (auth === "agent" && agentToken) {
    requestHeaders.set("Authorization", `Bearer ${agentToken}`);
  }

  const perform = async (): Promise<Response> =>
    fetch(`${API_BASE_URL}${path}`, {
      ...rest,
      credentials: "include",
      headers: requestHeaders,
      body: body === undefined ? undefined : JSON.stringify(body),
    });

  let response = await perform();

  if (response.status === 401 && auth === "user") {
    const refreshedToken = await refreshAccessToken();
    if (refreshedToken) {
      requestHeaders.set("Authorization", `Bearer ${refreshedToken}`);
      response = await perform();
    } else {
      clearAccessToken();
    }
  }

  const data = await parseResponse(response);
  if (!response.ok) {
    const detail =
      typeof data === "object" && data !== null && "detail" in data
        ? (data as { detail: unknown }).detail
        : data;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  return data as T;
}

export async function login(email: string, password: string): Promise<void> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  const response = await fetch(`${API_BASE_URL}/auth/jwt/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
    credentials: "include",
  });
  const data = (await response.json()) as { access_token?: string; detail?: string };
  if (!response.ok || !data.access_token) {
    throw new Error(data.detail || "Login failed");
  }
  setAccessToken(data.access_token);
}

export async function register(payload: {
  email: string;
  username: string;
  full_name?: string;
  password: string;
}): Promise<void> {
  await apiRequest("/auth/register", {
    method: "POST",
    auth: "none",
    body: payload,
  });
}

export async function startGoogleSignIn(): Promise<void> {
  const query = new URLSearchParams();
  query.append("scopes", "openid");
  query.append("scopes", "email");
  query.append("scopes", "profile");
  const data = await apiRequest<{ authorization_url: string }>(
    `/auth/google/authorize?${query.toString()}`,
    { method: "GET", auth: "none" },
  );
  window.location.href = data.authorization_url;
}
