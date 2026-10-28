/** Browser-side API calls through the same-origin proxy (`app/api/[...path]`). */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: string,
  ) {
    super(`${status} ${detail}`);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, { cache: "no-store", ...init });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, typeof body.detail === "string" ? body.detail : "error");
  }
  return (response.status === 204 ? undefined : await response.json()) as T;
}

export const api = {
  raw: <T>(path: string, body: string, contentType: string) =>
    request<T>(path, { method: "POST", headers: { "content-type": contentType }, body }),
  get: <T>(path: string) => request<T>(path),
  send: <T>(path: string, method: "POST" | "PATCH" | "DELETE", body?: unknown) =>
    request<T>(path, {
      method,
      headers: body === undefined ? undefined : { "content-type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
};
