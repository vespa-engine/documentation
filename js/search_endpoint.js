const searchEndpoint = ["localhost", "127.0.0.1", "[::1]"].includes(window.location.hostname)
  ? "/__search/"
  : "https://api.search.vespa.ai/search/";

export default searchEndpoint;
