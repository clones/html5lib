#!/usr/bin/env ruby -wKU

require File.join(File.dirname(__FILE__), 'preamble')

require 'html5/filters/validator'
require 'html5/html5parser'

class TestValidator < Test::Unit::TestCase
  def runValidatorTest(test)
    p = HTML5::HTMLParser.new(:tokenizer => HTMLConformanceChecker)
    p.parse(test['input'])
    errorCodes = p.errors.collect{|e| e[1]}
    if test.has_key?('fail-if')
      if errorCodes.include?(test['fail-if'])
        p test['input']
        p test['fail-if']
        p errorCodes
        flunk 
      end
    end
    if test.has_key?('fail-unless')
      unless errorCodes.include?(test['fail-unless'])
        p test['input']
        p test['fail-unless']
        p errorCodes
        flunk
      end
    end
  end

  for filename in html5_test_files('validator')
    tests    = JSON.load(open(filename))
    testName = File.basename(filename).sub(".test", "")
    tests['tests'].each_with_index do |test, index|
      define_method "test_#{index}" do
        runValidatorTest(test)
      end
    end
  end
end

