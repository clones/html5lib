require 'test/unit'
require 'html5lib/constants'

begin     
  require 'rubygems'
  require 'jsonx'
rescue LoadError
  class JSON
    def self.parse json
      json.gsub! /"\s*:/, '"=>'
      json.gsub!(/\\u[0-9a-fA-F]{4}/) {|x| [x[2..-1].to_i(16)].pack('U')}
      eval json
    end
  end
end 

class TokenizerTestParser
    def initialize(tokenizer)
        @tokenizer = tokenizer
    end

    def parse
        @outputTokens = []

        debug = nil
        for token in @tokenizer
            debug = token.inspect if token[:type] == :ParseError
            send ('process' + token[:type].to_s), token
        end

        return @outputTokens
    end

    def processDoctype(token)
        @outputTokens.push(["DOCTYPE", token[:name], token[:data]])
    end

    def processStartTag(token)
        @outputTokens.push(["StartTag", token[:name], token[:data]])
    end

    def processEmptyTag(token)
        if not HTML5lib::VOID_ELEMENTS.include? token[:name]
            @outputTokens.push("ParseError")
        end
        @outputTokens.push(["StartTag", token[:name], token[:data]])
    end

    def processEndTag(token)
        if token[:data].length > 0
            self.processParseError(token)
        end
        @outputTokens.push(["EndTag", token[:name]])
    end

    def processComment(token)
        @outputTokens.push(["Comment", token[:data]])
    end

    def processCharacters(token)
        @outputTokens.push(["Character", token[:data]])
    end

    alias processSpaceCharacters processCharacters

    def processCharacters(token)
        @outputTokens.push(["Character", token[:data]])
    end

    def processEOF(token)
    end

    def processParseError(token)
        @outputTokens.push("ParseError")
    end
end

class Html5TokenizerTestCase < Test::Unit::TestCase
    # convert array of attributes to a hash
    def normalizeTokens tokens
        for token in tokens:
            if token[0] == "StartTag"
                token[2] = Hash[*token[2].reverse.flatten]
            end
        end
        return tokens
    end

    # concatenate all consecutive character tokens into a single token
    def concatenateCharacterTokens tokens
        outputTokens = []
        for token in tokens
            if not token.include? "ParseError" and token[0] == "Character"
                if (outputTokens.length > 0 and 
                    not outputTokens[-1].include?("ParseError") and
                    outputTokens[-1][0] == "Character")
                    outputTokens[-1][1] += token[1]
                else
                    outputTokens.push(token)
                end
            else
                outputTokens.push(token)
            end
        end
        return outputTokens
    end

    # Test whether the test has passed or failed
    # 
    # For brevity in the tests, the test has passed if the sequence of expected
    # tokens appears anywhere in the sequence of returned tokens.
    def tokensMatch expectedTokens, recievedTokens
        return expectedTokens == recievedTokens
    end

end

tests = 0
base = File.dirname(File.dirname(File.dirname(File.expand_path(__FILE__))))
testfiles = File.join(File.join(File.join(base, 'tests'),'tokenizer'),'*')

$:.push File.join(base,'ruby')
require 'html5lib/tokenizer'

Dir[testfiles].each { |filename|
    testname =  File.basename(filename).sub /(.*)\.test/, 'test_\1'
    json = File.new(filename).read
    json.gsub!(/"\s*:/,'"=>')
    json.gsub!(/\\u[0-9a-fA-F]{4}/) {|x| [x[2..-1].to_i(16)].pack('U')}
    eval(json)['tests'].each {|test|
        for contentModelFlag in (test['contentModelFlags'] or [:PCDATA])
            tests+=1
            Html5TokenizerTestCase.send :define_method, ('test_%d' % tests) do 
                testname = test['description'] + "\n\t" + test['input']
                assert_nothing_raised testname do
                    output = concatenateCharacterTokens test['output']
                    tokenizer = HTML5lib::HTMLTokenizer.new(test['input'])
                    tokenizer.contentModelFlag = contentModelFlag.to_sym
                    if test['lastStartTag']
                        tokenizer.currentToken = {:type => :startTag,
                                      :name => test['lastStartTag']}
                    end
                    tokens = TokenizerTestParser.new(tokenizer).parse
                    tokens = normalizeTokens(tokens)
                    tokens = concatenateCharacterTokens(tokens)
                    if not tokensMatch(output, tokens)
                        message = "\n    Description:\n\t" +
                                  test['description'] +
                                  "\n\n    Input:\n\t" + test['input'] +
                                  "\n\n    Content Model Flag:\n\t" + 
                                  contentModelFlag.to_s + "\n"
                        assert_equal output, tokens, message
                    end
                end
            end
        end 
    }
}

