require 'html5/html5parser/phase'

module HTML5
class InSelectInTablePhase < Phase

  handle_start %w(caption table tbody tfoot thead tr td th) => 'Table'
  handle_end %w(caption table tbody tfoot thead tr td th) =>  'Table'

  def initialize(parser, tree)
    super(parser, tree)
  end

  def processCharacters(data)
    @parser.phases[:inSelect].processCharacters(data)
  end

  def startTagTable(name, attributes)
     @parser.parse_error("unexpected-table-element-start-tag-in-select-in-table", {:name => name})
     endTagOther("select")
     @parser.phase.processStartTag(name, attributes)
  end

  def startTagOther(name, attributes)
    @parser.phases[:inSelect].processStartTag(name, attributes)
  end

  def endTagTable(name)
     @parser.parse_error("unexpected-table-element-end-tag-in-select-in-table", {:name => name})
     if self.tree.elementInScope(name)
       endTagOther("select")
       @parser.phase.processEndTag(name)
     end
  end

  def endTagOther(name)
   @parser.phases[:inSelect].processEndTag(name)
  end
end
end