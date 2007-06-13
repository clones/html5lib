require 'html5lib/filters/base'

module HTML5lib
  module Filters
    class InjectMetaCharset < Base
      def initialize(source, encoding)
        super(source)
        @encoding = encoding
      end

      def each
        done = false
        __getobj__.each do |token|
          case token[:type]
          when :StartTag
            if token[:name].downcase == "meta" and token[:data]["charset"]
              done = true
            end

          when :EndTag
            if token[:name].downcase == "head"
              yield({:type => :EmptyTag, :name => "meta",
                     :data => {"charset" => @encoding}}) if not done
              done = true
            end
          end

          yield token
        end
      end
    end
  end
end
