require 'html5lib/constants'
module HTML5lib

module TokenConstructor
    LEADING_AND_TRAILING_SPACES = Regexp.new("^([#{SPACE_CHARACTERS.join('')}]*)(.*?)([#{SPACE_CHARACTERS.join('')}]*)$")

    def error(msg)
        return {:type => "SerializeError", :data => msg}
    end

    def normalizeAttrs(attrs)
        attrs.to_a
    end

    def emptyTag(name, attrs, hasChildren=false)
        if hasChildren
            yield error(_("Void element has children"))
        end
        return({:type => :EmptyTag, :name => name, \
                :data => normalizeAttrs(attrs)})
    end

    def startTag(name, attrs)
        return {:type => :StartTag, :name => name, \
                 :data => normalizeAttrs(attrs)}
    end

    def endTag(name)
        return {:type => :EndTag, :name => name, :data => []}
    end

    def text(data)
        LEADING_AND_TRAILING_SPACES.match(data)
        yield({:type => :SpaceCharacters, :data => $1}) unless $1.empty?
        yield({:type => :Characters, :data => $2}) unless $2.empty?
        yield({:type => :SpaceCharacters, :data => $3}) unless $3.empty?
    end

    def comment(data)
        return {:type => :Comment, :data => data}
    end

    def doctype(name)
        return {:type => :Doctype, :name => name, :data => name.upcase() == "HTML"}
    end

    def unknown(nodeType)
        return error(_("Unknown node type: ") + nodeType)
    end
end

class TreeWalker
    include TokenConstructor

    def initialize(tree)
        @tree = tree
    end

    def each
        raise NotImplementedError
    end

    alias walk each
end

class RecursiveTreeWalker < TreeWalker
    def walkChildren(node)
        raise NodeImplementedError
    end

    def element(node, name, attrs, hasChildren)
        if voidElements.include?(name)
            for token in emptyTag(name, attrs, hasChildren)
                yield token
            end
        else
            yield startTag(name, attrs)
            if hasChildren
                for token in walkChildren(node)
                    yield token
                end
            end
            yield endTag(name)
        end
    end
end

<<TBD
DOCUMENT = Node.DOCUMENT_NODE
DOCTYPE = Node.DOCUMENT_TYPE_NODE
TEXT = Node.TEXT_NODE
ELEMENT = Node.ELEMENT_NODE
COMMENT = Node.COMMENT_NODE
UNKNOWN = "<#UNKNOWN#>"

class NonRecursiveTreeWalker(TreeWalker)
    def getNodeDetails(self, node)
        raise NotImplementedError
    
    def getFirstChild(self, node)
        raise NotImplementedError
    
    def getNextSibling(self, node)
        raise NotImplementedError
    
    def getParentNode(self, node)
        raise NotImplementedError

    def walk(self)
        currentNode = self.tree
        while currentNode is not None
            details = self.getNodeDetails(currentNode)
            type, details = details[0], details[1:]
            hasChildren = False

            if type == DOCTYPE
                yield self.doctype(*details)

            elif type == TEXT
                for token in self.text(*details)
                    yield token

            elif type == ELEMENT
                name, attributes, hasChildren = details
                if name in voidElements
                    for token in self.emptyTag(name, attributes, hasChildren)
                        yield token
                    hasChildren = False
                else
                    yield self.startTag(name, attributes)

            elif type == COMMENT
                yield self.comment(details[0])

            elif type == :DOCUMENT
                hasChildren = True

            else
                yield self.unknown(details[0])
            
            firstChild = hasChildren and self.getFirstChild(currentNode) or None
            if firstChild is not None
                currentNode = firstChild
            else
                while currentNode is not None
                    details = self.getNodeDetails(currentNode)
                    type, details = details[0], details[1:]
                    if type == ELEMENT
                        name, attributes, hasChildren = details
                        if name not in voidElements
                            yield self.endTag(name)
                    nextSibling = self.getNextSibling(currentNode)
                    if nextSibling is not None
                        currentNode = nextSibling
                        break
                    if self.tree is currentNode
                        currentNode = None
                    else
                        currentNode = self.getParentNode(currentNode)
TBD
end
