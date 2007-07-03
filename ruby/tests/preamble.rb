require 'test/unit'

HTML5_BASE = File.dirname(File.dirname(File.dirname(File.expand_path(__FILE__)))) 

if File.exists?(File.join(HTML5_BASE, 'testdata'))
  TESTDATA_DIR = File.join(HTML5_BASE, 'testdata')
else
  TESTDATA_DIR = File.join(File.dirname(File.dirname(File.expand_path(__FILE__))), 'testdata')
end

$:.unshift File.join(File.dirname(File.dirname(__FILE__)),'lib')

$:.unshift File.dirname(__FILE__)

def html5_test_files(subdirectory)
  Dir[File.join(TESTDATA_DIR, subdirectory, '*.*')]
end

begin
  require 'rubygems'
  require 'json'
rescue LoadError
  class JSON
    def self.parse json
      json.gsub!(/"\s*:/, '"=>')
      json.gsub!(/\\u[0-9a-fA-F]{4}/) {|x| [x[2..-1].to_i(16)].pack('U')}
      null = nil
      eval json
    end
  end
end

module HTML5
  module TestSupport
    # convert the output of str(document) to the format used in the testcases
    def convertTreeDump(treedump)
      treedump.split(/\n/)[1..-1].map { |line| (line.length > 2 and line[0] == ?|) ? line[3..-1] : line }.join("\n")
    end

    def sortattrs(output)
      output.gsub(/^(\s+)\w+=.*(\n\1\w+=.*)+/) do |match|
         match.split("\n").sort.join("\n")
      end
    end

    class TestData
      include Enumerable

      def initialize(filename, sections)
        @f = open(filename)
        @sections = sections
      end
    
      def each
        data = {}
        key=nil
        @f.each_line do |line|
          heading = isSectionHeading(line)
          if heading
            if data.any? and heading == @sections[0]
              #Remove trailing newline
              data[key].chomp!
              yield normaliseOutput(data)
              data = {}
            end
            key = heading
            data[key]=""
          elsif key
            data[key] += line + "\n"
          end
        end
        yield normaliseOutput(data) if data
      end
        
      # If the current heading is a test section heading return the heading,
      # otherwise return false
      def isSectionHeading(line)
        line.chomp!
        if line[0] == ?# and @sections.include?(line[1..-1])
          return line[1..-1]
        else
          return false
        end
      end
    
      def normaliseOutput(data)
        #Remove trailing newlines
        data.keys.each { |key| data[key].chomp! }
        @sections.map {|heading| data[heading]}
      end
    end
  end
end
