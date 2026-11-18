import { afterEach, describe, expect, it, vi } from "vitest";

import { proxyApiRequest } from "@/lib/api-proxy";

describe("API proxy", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    delete process.env["SECURESCAN_API_INTERNAL_URL"];
  });

  it("forwards health requests to the backend /health endpoint", async () => {
    process.env["SECURESCAN_API_INTERNAL_URL"] = "http://backend:8000/api";

    const fetchMock = vi.fn().mockResolvedValue(Response.json({ status: "healthy" }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await proxyApiRequest(new Request("http://frontend:3000/api/health"));

    expect(response.status).toBe(200);
    expect(fetchMock.mock.calls[0]?.[0]).toBeInstanceOf(URL);
    expect(String(fetchMock.mock.calls[0]?.[0])).toBe("http://backend:8000/health");
  });

  it("uses the configured API base for regular API requests", async () => {
    process.env["SECURESCAN_API_INTERNAL_URL"] = "http://backend:8000/api";

    const fetchMock = vi.fn().mockResolvedValue(Response.json({ projects: [] }));
    vi.stubGlobal("fetch", fetchMock);

    await proxyApiRequest(new Request("http://frontend:3000/api/projects?page=2"));

    expect(String(fetchMock.mock.calls[0]?.[0])).toBe("http://backend:8000/api/projects?page=2");
  });

  it("uses the local backend fallback when no URL is configured", async () => {
    const fetchMock = vi.fn().mockResolvedValue(Response.json({ status: "ok" }));
    vi.stubGlobal("fetch", fetchMock);

    await proxyApiRequest(new Request("http://frontend:3000/api/projects"));

    expect(String(fetchMock.mock.calls[0]?.[0])).toBe("http://127.0.0.1:8000/api/projects");
  });

  it("preserves the HTTP method and request body", async () => {
    process.env["SECURESCAN_API_INTERNAL_URL"] = "http://backend:8000/api";

    const fetchMock = vi.fn().mockResolvedValue(Response.json({ uploaded: true }));
    vi.stubGlobal("fetch", fetchMock);

    await proxyApiRequest(
      new Request("http://frontend:3000/api/projects/upload", {
        method: "POST",
        body: "test-payload",
        headers: { "content-type": "text/plain" },
      }),
    );

    const options = fetchMock.mock.calls[0]?.[1];

    expect(options).toMatchObject({
      method: "POST",
      redirect: "manual",
      duplex: "half",
    });

    expect(options?.body).toBeInstanceOf(ReadableStream);
    expect(await new Response(options?.body).text()).toBe("test-payload");
  });

  it("preserves multipart upload content and boundary", async () => {
    process.env["SECURESCAN_API_INTERNAL_URL"] = "http://backend:8000/api";

    const boundary = "securescan-test-boundary";
    const multipartBody = [
      `--${boundary}`,
      'Content-Disposition: form-data; name="file"; filename="test-project.zip"',
      "Content-Type: application/zip",
      "",
      "synthetic ZIP payload",
      `--${boundary}--`,
      "",
    ].join("\r\n");

    const fetchMock = vi
      .fn()
      .mockImplementation(async (_url: URL, options: RequestInit & { duplex?: string }) => {
        const headers = new Headers(options.headers);
        const body = await new Response(options.body).text();

        expect(headers.get("content-type")).toBe(`multipart/form-data; boundary=${boundary}`);
        expect(body).toContain('filename="test-project.zip"');
        expect(body).toContain("synthetic ZIP payload");

        return Response.json({ uploaded: true });
      });

    vi.stubGlobal("fetch", fetchMock);

    const response = await proxyApiRequest(
      new Request("http://frontend:3000/api/projects/upload", {
        method: "POST",
        headers: {
          "content-type": `multipart/form-data; boundary=${boundary}`,
        },
        body: multipartBody,
      }),
    );

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(String(fetchMock.mock.calls[0]?.[0])).toBe("http://backend:8000/api/projects/upload");
  });

  it("does not forward hop-by-hop request headers", async () => {
    process.env["SECURESCAN_API_INTERNAL_URL"] = "http://backend:8000/api";

    const fetchMock = vi.fn().mockResolvedValue(Response.json({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await proxyApiRequest(
      new Request("http://frontend:3000/api/projects", {
        headers: {
          connection: "keep-alive, x-internal-hop",
          "keep-alive": "timeout=5",
          "x-internal-hop": "must-not-be-forwarded",
          "content-type": "application/json",
        },
      }),
    );

    const headers = new Headers(fetchMock.mock.calls[0]?.[1]?.headers);

    expect(headers.has("connection")).toBe(false);
    expect(headers.has("keep-alive")).toBe(false);
    expect(headers.has("x-internal-hop")).toBe(false);
    expect(headers.get("content-type")).toBe("application/json");
  });

  it("does not forward hop-by-hop response headers", async () => {
    process.env["SECURESCAN_API_INTERNAL_URL"] = "http://backend:8000/api";

    const backendResponse = new Response("ok", {
      headers: {
        connection: "keep-alive, x-internal-hop",
        "keep-alive": "timeout=5",
        "x-internal-hop": "must-not-reach-client",
        "content-type": "text/plain",
      },
    });

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(backendResponse));

    const response = await proxyApiRequest(new Request("http://frontend:3000/api/projects"));

    expect(response.headers.has("connection")).toBe(false);
    expect(response.headers.has("keep-alive")).toBe(false);
    expect(response.headers.has("x-internal-hop")).toBe(false);
    expect(response.headers.get("content-type")).toBe("text/plain");
  });

  it("returns 502 when the backend is unavailable", async () => {
    process.env["SECURESCAN_API_INTERNAL_URL"] = "http://backend:8000/api";

    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("connection failed")));
    vi.spyOn(console, "error").mockImplementation(() => {});

    const response = await proxyApiRequest(new Request("http://frontend:3000/api/health"));

    expect(response.status).toBe(502);
    expect(await response.json()).toEqual({
      detail: "Backend API is currently unavailable.",
    });
  });

  it("rejects unsupported backend URL protocols", async () => {
    process.env["SECURESCAN_API_INTERNAL_URL"] = "ftp://backend:8000/api";

    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(console, "error").mockImplementation(() => {});

    const response = await proxyApiRequest(new Request("http://frontend:3000/api/health"));

    expect(response.status).toBe(502);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
