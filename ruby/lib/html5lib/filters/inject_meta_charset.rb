require 'html5lib/filters/base'

module HTML5lib
  module Filters
    class InjectMetaCharset < Base
      def initialize(source, encoding)
        super(source)
        @encoding = encoding
      end

      def each
        state = :pre_head
        meta_found = @encoding.nil?
        pending = []

        __getobj__.each do |token|
          case token[:type]
          when :StartTag
            state = :in_head if token[:name].downcase == "head"

          when :EmptyTag
            if token[:name].downcase == "meta"
              # replace charset with actual encoding
              token[:data].each_with_index do |(name,value),index|
                if name == 'charset'
                  token[:data][index][1]=@encoding
                  meta_found = true
                end
              end

            elsif token[:name].downcase == "head" and not meta_found
              # insert meta into empty head
              yield(:type => :StartTag, :name => "head", :data => token[:data])
              yield(:type => :EmptyTag, :name => "meta",
                    :data => [["charset", @encoding]])
              yield(:type => :EndTag, :name => "head")
              meta_found = true
              next
            end

          when :EndTag
            if token[:name].downcase == "head" and pending.any?
              # insert meta into head (if necessary) and flush pending queue
              yield pending.shift
              yield(:type => :EmptyTag, :name => "meta",
                    :data => [["charset", @encoding]]) if not meta_found
              yield pending.shift while pending.any?
              meta_found = true
              state = :post_head
            end
          end

          if state == :in_head
            pending << token
          else
            yield token
          end
        end
      end
    end
  end
end
