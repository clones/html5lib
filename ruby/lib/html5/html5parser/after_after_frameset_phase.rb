require 'html5/html5parser/phase'

module HTML5
  class AfterAfterFramesetPhase < Phase
  
    handle_start 'html', 'noframes'
    
    def processComment(data)
      @tree.insert_comment(data)
    end
  
    def processDoctype data
      @parser.phases[:inBody].processDoctype(data)
    end
    
    def processSpaceCharacters data
      @parser.phases[:inBody].processSpaceCharacters(data)
    end

    def startTagHtml data
      @parser.phases[:inBody].startTagHtml(data)
    end

    def startTagNoframes name, attributes
      @parser.phases[:inHead].startTagNoframes(data)
    end

    def startTagOther name, attributes
      parse_error("unexpected-char-after-body")
    end
  end
end