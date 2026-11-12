# Copyright Vespa.ai. All rights reserved.

require 'json'
require 'net/http'

# Keep local browser requests on the Jekyll origin; the public API disallows localhost CORS.
module SearchProxy
  def self.handle(req, res)
    uri = URI('https://api.search.vespa.ai/search/')
    uri.query = req.query_string
    upstream = Net::HTTP.start(uri.host, uri.port, use_ssl: true, open_timeout: 5, read_timeout: 15) do |http|
      http.request(Net::HTTP::Get.new(uri))
    end
    res.status = upstream.code.to_i
    res['Content-Type'] = 'application/json'
    res['Cache-Control'] = 'no-store'
    res.body = upstream.body
  rescue StandardError => e
    Jekyll.logger.warn 'Search proxy:', e.message
    res.status = 502
    res['Content-Type'] = 'application/json'
    res.body = JSON.generate(error: 'Search API unavailable')
  end

  module ServletPatch
    def do_GET(req, res) # rubocop:disable Naming/MethodName
      if req.path == '/__search/' && %w[127.0.0.1 ::1].include?(req.peeraddr[3])
        SearchProxy.handle(req, res)
      else
        super
      end
    end
  end

  module ServeSetup
    private

    def setup(destination)
      super
      servlet = Jekyll::Commands::Serve::Servlet
      servlet.prepend(ServletPatch) unless servlet < ServletPatch
    end
  end
end

Jekyll::Commands::Serve.singleton_class.prepend(SearchProxy::ServeSetup)
