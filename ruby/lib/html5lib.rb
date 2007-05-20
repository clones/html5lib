require 'html5lib/html5parser'

module HTML5lib
    def self.parse(input)
        HTMLParser.parse(input)
    end
end