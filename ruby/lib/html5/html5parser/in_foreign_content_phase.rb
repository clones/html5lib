require 'html5/html5parser/phase'

module HTML5
  class InForeignContentPhase < Phase

    def processCharacters(data)
      @tree.insertText(data)
    end

    def startTagOther(name, attributes, self_closing)
      if !%w[mglyph malignmark].include?(name) && %w[mi mo mn ms mtext].include?(@tree.open_elements.last.name) &&
         @tree.open_elements.last.namespace == :math

        @parser.secondary_phase.processStartTag(name, attributes)
        if @parser.phase == @parser.phases[:inForeignContent]
          if !@tree.open_elements.any? {|e| e.namespace }
            @parser.phase = @parser.secondary_phase
          end
        end
      elsif %w[b big blockquote body br center code dd div dl dt em embed font
          h1 h2 h3 h4 h5 h6 head hr i img li listing menu meta nobr ol p pre ruby s small
          span strong strike sub sup table tt u ul var].include?(name)

        parse_error("html-in-foreign-content", :name => name)

        until @tree.open_elements.last.namespace == nil
          @tree.open_elements.pop
        end
        @parser.phase = @parser.secondary_phase
        @parser.phase.processStartTag(name, attributes)
      else
        if @tree.open_elements.last.namespace == :math
          attribtues = adjust_mathml_attributes(attributes)
        end
        attributes = adjust_foreign_attributes(attributes)
        @tree.insert_foreign_element(name, attributes, @tree.open_elements.last.namespace)
        @tree.open_elements.pop if self_closing
      end
    end

    def endTagOther(name)
      @parser.secondary_phase.processEndTag(name)
      if @parser.phase == @parser.phases[:inForeignContent]
        if !@tree.open_elements.any? {|e| e.namespace }
          @parser.phase = @parser.secondary_phase
        end
      end
    end
  end
end