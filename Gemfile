# Copyright Vespa.ai. All rights reserved.
ruby '>=2.6'

source "https://rubygems.org"

# Hello! This is where you manage which Jekyll version is used to run.
# When you want to use a different version, change it below, save the
# file and run `bundle install`. Run Jekyll with `bundle exec`, like so:
#
#     bundle exec jekyll serve
#
# This will help ensure the proper Jekyll version is running.
# Happy Jekylling!
# gem "jekyll", "~> 3.9.0"

# This is the default theme for new Jekyll sites. You may change this to anything you like.
gem "minima", ">= 2.5.1"

# Direct Jekyll dependency. The `github-pages` meta-gem caps at Ruby < 4.0
# (via commonmarker ~> 0.22), so we depend on Jekyll directly.
gem "jekyll", "~> 3.10"

# Performance-booster for watching directories on Windows
gem "wdm", "~> 0.2.0", :install_if => Gem.win_platform?

# kramdown v2 ships without the gfm parser by default. If you're using
# kramdown v1, comment out this line.
gem "kramdown-parser-gfm"

# Work-around for webrick no longer included in Ruby 3.0 (https://github.com/jekyll/jekyll/issues/8523)
gem "webrick"

# Get the html-proofer to work
gem 'rake'
gem 'html-proofer', '>= 5.2.1'

# Work-around for csv and base64 no longer included in Ruby 3.4.0
gem "csv"
gem "base64"

# Jekyll plugins group

group :jekyll_plugins do
  gem "jekyll-feed", "~> 0.12"
  gem "jekyll-redirect-from"
  gem "jekyll-sitemap"
  gem "jekyll-seo-tag"
  gem "reverse_markdown"
  gem "parallel"
  gem "ruby-progressbar" # <-- Add this line
end