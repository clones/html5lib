require 'html5/html5parser/phase'

module HTML5
  class AfterHeadPhase < Phase

    handle_start 'html', 'body', 'frameset', %w( base link meta script style title ) => 'FromHead'

    def process_eof
      anythingElse
      @parser.phase.process_eof
    end

    def processCharacters(data)
      anythingElse
      @parser.phase.processCharacters(data)
    end

    def startTagBody(name, attributes)
      @tree.insert_element(name, attributes)
      @parser.phase = @parser.phases[:inBody]
    end

    def startTagFrameset(name, attributes)
      @tree.insert_element(name, attributes)
      @parser.phase = @parser.phases[:inFrameset]
    end

    def startTagFromHead(name, attributes)
      parse_error(_("Unexpected start tag (#{name}) that can be in head. Moved."))
      @parser.phase = @parser.phases[:inHead]
      @parser.phase.processStartTag(name, attributes)
    end

    def startTagOther(name, attributes)
      anythingElse
      @parser.phase.processStartTag(name, attributes)
    end

    def processEndTag(name)
      anythingElse
      @parser.phase.processEndTag(name)
    end

    def anythingElse
      @tree.insert_element('body', {})
      @parser.phase = @parser.phases[:inBody]
    end

  end
end