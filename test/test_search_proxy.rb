# Run with: bundle exec ruby test/test_search_proxy.rb
require 'jekyll'
require 'webrick'
require_relative '../_plugins/search_proxy'

request = Struct.new(:path, :query_string, :peeraddr).new(
  '/__search/', 'userinput=predicate%20fields&hits=5', [nil, nil, nil, '127.0.0.1']
)
response = WEBrick::HTTPResponse.new(WEBrick::Config::HTTP)
upstream = Struct.new(:code, :body).new('200', '{"root":{"children":[]}}')
http = Object.new
http.define_singleton_method(:request) do |req|
  raise 'Query or upstream path changed' unless req.path == "/search/?#{request.query_string}"
  raise 'Expected GET' unless req.method == 'GET'
  raise 'Forwarded browser cookies' if req['Cookie']
  upstream
end
original_start = Net::HTTP.method(:start)
Net::HTTP.define_singleton_method(:start) do |host, port, **options, &block|
  raise 'Unexpected upstream' unless host == 'api.search.vespa.ai' && port == 443
  raise 'Missing TLS or timeouts' unless options == { use_ssl: true, open_timeout: 5, read_timeout: 15 }
  block.call(http)
end

begin
  SearchProxy.handle(request, response)
  raise 'Response changed' unless response.status == 200 && response.body == upstream.body
  raise 'Expected JSON' unless response['Content-Type'] == 'application/json'

  upstream.code = '429'
  upstream.body = '{"error":"rate limited"}'
  SearchProxy.handle(request, response)
  raise 'Lost upstream error' unless response.status == 429 && response.body == upstream.body

  http.define_singleton_method(:request) { |_req| raise Timeout::Error, 'test timeout' }
  SearchProxy.handle(request, response)
  raise 'Expected gateway error' unless response.status == 502 && JSON.parse(response.body).key?('error')
ensure
  Net::HTTP.define_singleton_method(:start, original_start)
end

# Exercise the actual Jekyll servlet hook without starting a network listener.
Jekyll::Commands::Serve.send(:setup, File.expand_path('../_site', __dir__))
raise 'Servlet patch missing' unless Jekyll::Commands::Serve::Servlet < SearchProxy::ServletPatch
servlet = Class.new do
  def do_GET(_req, res)
    res.status = 404
  end
  prepend SearchProxy::ServletPatch
end.new
original_handle = SearchProxy.method(:handle)
SearchProxy.define_singleton_method(:handle) { |_req, res| res.status = 200 }
begin
  %w[127.0.0.1 ::1].each do |address|
    request.peeraddr[3] = address
    servlet.do_GET(request, response)
    raise 'Loopback request rejected' unless response.status == 200
  end
  request.peeraddr[3] = '192.0.2.1'
  servlet.do_GET(request, response)
  raise 'Remote request allowed' unless response.status == 404
  request.peeraddr[3] = '127.0.0.1'
  request.path = '/en/index.html'
  servlet.do_GET(request, response)
  raise 'Normal page intercepted' unless response.status == 404
ensure
  SearchProxy.define_singleton_method(:handle, original_handle)
end

puts 'Search proxy OK'
