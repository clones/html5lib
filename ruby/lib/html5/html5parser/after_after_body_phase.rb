require 'html5/html5parser/phase'

module HTML5
  class AfterAfterBodyPhase < Phase
    
    handle_start 'html'
    
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

    def startTagOther name, attributes
      parse_error("unexpected-start-tag")
      @parser.phase = @parser.phases[:inBody]
      @parser.phase.processStartTag(name, attributes)
    end

    def endTagOther name
      parse_error("unexpected-end-tag")
      @parser.phase = @parser.phases[:inBody]
      @parser.phase.processEndTag(name)
    end
    
    def processCharacters data
      parse_error "unexpected-char-after-body"
      @parser.phase = @parser.phases[:inBody]
      @parser.phase.processCharacters(data)
    end
    
  end
end