require 'html5lib/constants'

# The scope markers are inserted when entering buttons, object elements,
# marquees, table cells, and table captions, and are used to prevent formatting
# from "leaking" into tables, buttons, object elements, and marquees.
Marker = nil

#XXX - TODO; make the default interface more ElementTree-like
#            rather than DOM-like

module HTML5lib
module TreeBuilders
module Base

class Node
    # The parent of the current node (or nil for the document node)
    attr_accessor :parent

    # a list of child nodes of the current node. This must 
    # include all elements but not necessarily other node types
    attr_accessor :childNodes

    # A list of miscellaneous flags that can be set on the node
    attr_accessor :_flags

    def initialize name
        @parent = nil
        @childNodes = []
        @_flags = []
    end

    # Insert node as a child of the current node
    def appendChild node
        raise NotImplementedError
    end

    # Insert data as text in the current node, positioned before the 
    # start of node insertBefore or to the end of the node's text.
    def insertText data, insertBefore=nil
        raise NotImplementedError
    end

    # Insert node as a child of the current node, before refNode in the 
    # list of child nodes. Raises ValueError if refNode is not a child of 
    # the current node
    def insertBefore node, refNode
        raise NotImplementedError
    end

    # Remove node from the children of the current node
    def removeChild node
        raise NotImplementedError
    end

    # Move all the children of the current node to newParent. 
    # This is needed so that trees that don't store text as nodes move the 
    # text in the correct way
    def reparentChildren newParent
        #XXX - should this method be made more general?
        for child in @childNodes
            newParent.appendChild(child)
        end
        @childNodes = []
    end

    # Return a shallow copy of the current node i.e. a node with the same
    # name and attributes but with no parent or child nodes
    def cloneNode
        raise NotImplementedError
    end

    # Return true if the node has children or text, false otherwise
    def hasContent
        raise NotImplementedError
    end
end

# Base treebuilder implementation
# documentClass - the class to use for the bottommost node of a document
# elementClass - the class to use for HTML Elements
# commentClass - the class to use for comments
# doctypeClass - the class to use for doctypes
class TreeBuilder
    attr_accessor :openElements
    attr_accessor :activeFormattingElements
    attr_accessor :document
    attr_accessor :headPointer
    attr_accessor :formPointer

    #Document class
    documentClass = nil

    #The class to use for creating a node
    elementClass = nil

    #The class to use for creating comments
    commentClass = nil

    #The class to use for creating doctypes
    doctypeClass = nil
    
    #Fragment class
    fragmentClass = nil

    def initialize
        reset
    end
    
    def reset
        @openElements = []
        @activeFormattingElements = []

        #XXX - rename these to headElement, formElement
        @headPointer = nil
        @formPointer = nil

        self.insertFromTable = false

        @document = @documentClass.new
    end

    def elementInScope target, tableVariant=false
        # Exit early when possible.
        return true if @openElements[-1].name == target

        # AT How about while true and simply set node to [-1] and set it to
        # [-2] at the end...
        for node in @openElements.reverse
            if node.name == target
                return true
            elsif node.name == "table"
                return false
            elsif not tableVariant and SCOPING_ELEMENTS.include? node.name
                return false
            elsif node.name == "html"
                return false
            end
        end
        assert false # We should never reach this point
    end

    def reconstructActiveFormattingElements
        # Within this algorithm the order of steps described in the
        # specification is not quite the same as the order of steps in the
        # code. It should still do the same though.

        # Step 1: stop the algorithm when there's nothing to do.
        return if not @activeFormattingElements

        # Step 2 and step 3: we start with the last element. So i is -1.
        i = -1
        entry = @activeFormattingElements[i]
        return if entry == Marker or @openElements.include? entry

        # Step 6
        while entry != Marker and not @openElements.include? entry
            # Step 5: let entry be one earlier in the list.
            i -= 1
            begin
                entry = @activeFormattingElements[i]
            rescue
                # Step 4: at this point we need to jump to step 8. By not doing
                # i += 1 which is also done in step 7 we achieve that.
                break
            end
        end
        while true
            # Step 7
            i += 1

            # Step 8
            clone = @activeFormattingElements[i].cloneNode

            # Step 9
            element = insertElement(clone.name, clone.attributes)

            # Step 10
            @activeFormattingElements[i] = element

            # Step 11
            break if element == @activeFormattingElements[-1]
        end
    end

    def clearActiveFormattingElements
        entry = @activeFormattingElements.pop
        while @activeFormattingElements and entry != Marker
            entry = @activeFormattingElements.pop
        end
    end

    # Check if an element exists between the end of the active
    # formatting elements and the last marker. If it does, return it, else
    # return false
    def elementInActiveFormattingElements name

        for item in @activeFormattingElements.reverse
            # Check for Marker first because if it's a Marker it doesn't have a
            # name attribute.
            if item == Marker
                break
            elsif item.name == name
                return item
            end
        end
        return false
    end

    def insertDoctype name
        @document.appendChild(@doctypeClass.new(name))
    end

    def insertComment data, parent=nil
        if parent == nil
            parent = @openElements[-1]
        end
        parent.appendChild(@commentClass.new(data))
    end
                           
    # Create an element but don't insert it anywhere
    def createElement name, attributes
        element = @elementClass.new(name)
        element.attributes = attributes
        return element
    end

    def insertFromTable
        return insertFromTable
    end

    # Switch the function used to insert an element from the
    # normal one to the misnested table one and back again
    def insertFromTable= value
        @insertFromTable = value
        if value
            @insertElement = :insertElementTable
        else
            @insertElement = :insertElementNormal
        end
    end

    def insertElement name, attributes
        send @insertElement, name, attributes
    end

    def insertElementNormal name, attributes
        element = @elementClass.new(name)
        element.attributes = attributes
        @openElements[-1].appendChild(element)
        @openElements.push(element)
        return element
    end

    # Create an element and insert it into the tree
    def insertElementTable name, attributes
        element = @elementClass.new(name)
        element.attributes = attributes
        if not TABLE_INSERT_MODE_ELEMENTS.include? @openElements[-1].name
            return insertElementNormal(name, attributes)
        else
            #We should be in the InTable mode. This means we want to do
            #special magic element rearranging
            parent, insertBefore = getTableMisnestedNodePosition
            if insertBefore == nil
                parent.appendChild(element)
            else
                parent.insertBefore(element, insertBefore)
            end
            @openElements.push(element)
        end
        return element
    end

    def insertText data, parent=nil
        """Insert text data."""
        if parent == nil
            parent = @openElements[-1]
        end

        if (not(@insertFromTable) or (@insertFromTable and
                not TABLE_INSERT_MODE_ELEMENTS.include?  @openElements[-1].name))
            parent.insertText(data)
        else
            #We should be in the InTable mode. This means we want to do
            #special magic element rearranging
            parent, insertBefore = getTableMisnestedNodePosition
            parent.insertText(data, insertBefore)
        end
    end
            
    # Get the foster parent element, and sibling to insert before
    # (or nil) when inserting a misnested table node
    def getTableMisnestedNodePosition
        #The foster parent element is the one which comes before the most
        #recently opened table element
        #XXX - this is really inelegant
        lastTable=nil
        fosterParent = nil
        insertBefore = nil
        for elm in @openElements.reverse
            if elm.name == "table"
                lastTable = elm
                break
            end
        end
        if lastTable
            #XXX - we should really check that this parent is actually a
            #node here
            if lastTable.parent
                fosterParent = lastTable.parent
                insertBefore = lastTable
            else
                fosterParent = @openElements[
                    @openElements.index(lastTable) - 1]
            end
        else
            fosterParent = @openElements[0]
        end
        return fosterParent, insertBefore
    end

    def generateImpliedEndTags exclude=nil
        name = @openElements[-1].name
        if (["dd", "dt", "li", "p", "td", "th", "tr"].include? name and
            name != exclude)
            @openElements.pop
            # XXX This is not entirely what the specification says. We should
            # investigate it more closely.
            generateImpliedEndTags(exclude)
        end
    end

    def getDocument
        "Return the final tree"
        return @document
    end
    
    def getFragment
        "Return the final fragment"
        #assert @innerHTML
        fragment = @fragmentClass.new
        @openElements[0].reparentChildren(fragment)
        return fragment
    end

    # Serialize the subtree of node in the format required by unit tests
    # node - the node from which to start serializing
    def testSerializer node
        raise NotImplementedError
    end
end

end
end
end
