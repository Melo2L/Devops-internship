const HOP_BY_HOP_HEADERS = [
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "proxy-connection",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
];

function filterHopByHopHeaders(source: Headers): Headers {
  const headers = new Headers(source);

  const connectionTokens = (headers.get("connection") ?? "")
    .split(",")
    .map((token) => token.trim().toLowerCase())
    .filter(Boolean);

  for (const name of HOP_BY_HOP_HEADERS) {
    headers.delete(name);
  }

  for (const name of connectionTokens) {
    headers.delete(name);
  }

  return headers;
}

const DEFAULT_API_BASE = "http://127.0.0.1:8000/api";

export async function proxyApiRequest(request: Request): Promise<Response> {
  const url = new URL(request.url);

  const configuredBase = process.env["SECURESCAN_API_INTERNAL_URL"] ?? DEFAULT_API_BASE;

  try {
    const apiBase = new URL(configuredBase);

    if (!["http:", "https:"].includes(apiBase.protocol)) {
      throw new Error("Unsupported backend URL protocol");
    }

    const isHealthEndpoint = url.pathname === "/api/health";

    const backendPath = isHealthEndpoint ? "/health" : url.pathname.replace(/^\/api(?=\/|$)/, "");

    const targetUrl = new URL(apiBase.origin);
    targetUrl.pathname = isHealthEndpoint
      ? backendPath
      : `${apiBase.pathname.replace(/\/+$/, "")}${backendPath}`;
    targetUrl.search = url.search;

    const headers = filterHopByHopHeaders(request.headers);
    headers.delete("host");

    const hasBody = request.method !== "GET" && request.method !== "HEAD" && request.body !== null;

    const response = await fetch(targetUrl, {
      method: request.method,
      headers,
      redirect: "manual",
      ...(hasBody && request.body
        ? {
            body: request.body,
            duplex: "half" as const,
          }
        : {}),
    });

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: filterHopByHopHeaders(response.headers),
    });
  } catch (error) {
    console.error("Backend API proxy failed:", error);

    return Response.json({ detail: "Backend API is currently unavailable." }, { status: 502 });
  }
}
