/**
 * Cloudflare Worker Recipe for Content Negotiation (acceptmarkdown.com compliant)
 * 
 * If using Cloudflare Workers or Pages in front of borkert.dev:
 * 1. Matches Accept: text/markdown on HTML routes.
 * 2. Serves /index.md with Content-Type: text/markdown; charset=utf-8.
 * 3. Enforces Vary: Accept, Accept-Encoding to prevent CDN cache pollution.
 * 4. Advertises alternate representations via Link headers (RFC 8288).
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const accept = request.headers.get('Accept') || '';

    // Non-content assets bypass negotiation
    const isStaticAsset = /\.(css|js|json|xml|txt|png|jpe?g|gif|svg|woff2?|ico)$/i.test(url.pathname);

    if (!isStaticAsset && accept.includes('text/markdown')) {
      let mdPath = url.pathname;
      if (mdPath === '/' || mdPath === '/index.html') {
        mdPath = '/index.md';
      } else if (!mdPath.endsWith('.md')) {
        mdPath = `${mdPath}.md`;
      }

      const mdRequest = new Request(new URL(mdPath, url.origin), request);
      const mdResponse = env.ASSETS ? await env.ASSETS.fetch(mdRequest) : await fetch(mdRequest);

      if (mdResponse.ok) {
        const headers = new Headers(mdResponse.headers);
        headers.set('Content-Type', 'text/markdown; charset=utf-8');
        headers.set('Vary', 'Accept, Accept-Encoding');
        headers.set('Link', `</index.md>; rel="alternate"; type="text/markdown", </llms.txt>; rel="alternate"; type="text/markdown"`);
        return new Response(mdResponse.body, {
          status: 200,
          headers
        });
      }
    }

    // Default HTML or static response
    const response = env.ASSETS ? await env.ASSETS.fetch(request) : await fetch(request);
    const headers = new Headers(response.headers);
    headers.set('Vary', 'Accept, Accept-Encoding');
    headers.set('Link', `</index.md>; rel="alternate"; type="text/markdown", </llms.txt>; rel="alternate"; type="text/markdown"`);

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers
    });
  }
};
