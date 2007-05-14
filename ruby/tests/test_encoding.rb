require 'test/unit'
require 'html5lib/inputstream'

BASE = File.dirname(File.dirname(File.dirname(File.expand_path(__FILE__))))
TESTFILES = File.join(File.join(File.join(BASE, 'tests'),'encoding'),'*.dat')
CHARDET = File.join(File.join(File.dirname(TESTFILES),'chardet'))

class EncodingTestCase < Test::Unit::TestCase
    def testChardet
        f = File.open(File.join(CHARDET,'test_big5.txt'))
        stream = HTML5lib::HTMLInputStream.new(f, :chardet=>true)
        assert_equal "big5", stream.charEncoding.downcase
    end
end

tests = 0

Dir[TESTFILES].each { |filename|
    File.open(filename).read.split("#data\n").each {|test|
        next if test == ""
        input, encoding = test.split(/\n#encoding\s+/,2)
        encoding = encoding.split[0]
        tests += 1
        EncodingTestCase.send :define_method, testName = 'test_%d' % tests do
            stream = HTML5lib::HTMLInputStream.new(input, :chardet=>false)
            assert_equal encoding.downcase, stream.charEncoding.downcase, input
        end
    }
}

begin
    require 'rubygems'
    require 'UniversalDetector'
rescue LoadError
    puts "chardet not found, skipping chardet tests"
    EncodingTestCase.send :remove_method, :testChardet
end
