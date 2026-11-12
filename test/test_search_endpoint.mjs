import assert from 'node:assert/strict';
import test from 'node:test';

test('only loopback hosts use the local search proxy', async () => {
  try {
    const cases = [
      ['localhost', '/__search/'],
      ['127.0.0.1', '/__search/'],
      ['[::1]', '/__search/'],
      ['docs.vespa.ai', 'https://api.search.vespa.ai/search/'],
      ['preview.example.com', 'https://api.search.vespa.ai/search/'],
      ['localhost.example.com', 'https://api.search.vespa.ai/search/'],
    ];
    for (const [hostname, expected] of cases) {
      globalThis.window = { location: { hostname } };
      const { default: endpoint } = await import(`../js/search_endpoint.js?host=${encodeURIComponent(hostname)}`);
      assert.equal(endpoint, expected);
    }
  } finally {
    delete globalThis.window;
  }
});
