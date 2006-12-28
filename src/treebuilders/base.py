import sys
import os

# XXX someone please fix this up! And make sure it doesn't break Windows.
from src.constants import contentModelFlags, spaceCharacters
from src.constants import scopingElements, formattingElements, specialElements
from src.constants import headingElements, tableInsertModeElements

# The scope markers are inserted when entering buttons, object elements,
# marquees, table cells, and table captions, and are used to prevent formatting
# from "leaking" into tables, buttons, object elements, and marquees.
Marker = None

#XXX - TODO; make the default interface more ElementTree-like
#            rather than DOM-like

class TreeBuilder(object):
    """Base treebuilder implementation"""

    #Document class
    documentClass = None

    #The class to use for creating a node
    elementClass = None

    #The class to use for creating comments
    commentClass = None

    #The class to use for creating doctypes
    doctypeClass = None

    def __init__(self):
        self.openElements = []
        self.activeFormattingElements = []

        #XXX - rename these to headElement, formElement
        self.headPointer = None
        self.formPointer = None

        self.insertFromTable = False

        self.document = self.documentClass()

    def elementInScope(self, target, tableVariant=False):
        # Exit early when possible.
        if self.openElements[-1].name == target:
            return True

        # AT Use reverse instead of [::-1] when we can rely on Python 2.4
        # AT How about while True and simply set node to [-1] and set it to
        # [-2] at the end...
        for node in self.openElements[::-1]:
            if node.name == target:
                return True
            elif node.name == "table":
                return False
            elif not tableVariant and node.name in scopingElements:
                return False
            elif node.name == "html":
                return False
        assert False # We should never reach this point

    def reconstructActiveFormattingElements(self):
        # Within this algorithm the order of steps described in the
        # specification is not quite the same as the order of steps in the
        # code. It should still do the same though.

        # Step 1: stop the algorithm when there's nothing to do.
        if not self.activeFormattingElements:
            return

        # Step 2 and step 3: we start with the last element. So i is -1.
        i = -1
        entry = self.activeFormattingElements[i]
        if entry == Marker or entry in self.openElements:
            return

        # Step 6
        while entry != Marker and entry not in self.openElements:
            # Step 5: let entry be one earlier in the list.
            i -= 1
            try:
                entry = self.activeFormattingElements[i]
            except:
                # Step 4: at this point we need to jump to step 8. By not doing
                # i += 1 which is also done in step 7 we achieve that.
                break
        while True:
            # Step 7
            i += 1

            # Step 8
            clone = self.activeFormattingElements[i].cloneNode()

            # Step 9
            element = self.insertElement(clone.name, clone.attributes)

            # Step 10
            self.activeFormattingElements[i] = element

            # Step 11
            if element == self.activeFormattingElements[-1]:
                break

    def clearActiveFormattingElements(self):
        entry = self.activeFormattingElements.pop()
        while self.activeFormattingElements and entry != Marker:
            entry = self.activeFormattingElements.pop()

    def elementInActiveFormattingElements(self, name):
        """Check if an element exists between the end of the active
        formatting elements and the last marker. If it does, return it, else
        return false"""

        for item in self.activeFormattingElements[::-1]:
            # Check for Marker first because if it's a Marker it doesn't have a
            # name attribute.
            if item == Marker:
                break
            elif item.name == name:
                return item
        return False

    def insertDoctype(self, name):
        self.document.appendChild(self.doctypeClass(name))

    def insertComment(self, data, parent=None):
        if parent is None:
            parent = self.openElements[-1]
        parent.appendChild(self.commentClass(data))
                           
    def createElement(self, name, attributes):
        """Create an element but don't insert it anywhere"""
        element = self.elementClass(name)
        element.attributes = attributes
        return element

    def _getInsertFromTable(self):
        return self._insertFromTable

    def _setInsertFromTable(self, value):
        """Switch the function used to insert an element from the
        normal one to the misnested table one and back again"""
        self._insertFromTable = value
        if value:
            self.insertElement = self.insertElementTable
        else:
            self.insertElement = self.insertElementNormal

    insertFromTable = property(_getInsertFromTable, _setInsertFromTable)
        
    def insertElementNormal(self, name, attributes):
        element = self.elementClass(name)
        element.attributes = attributes
        self.openElements[-1].appendChild(element)
        self.openElements.append(element)
        return element

    def insertElementTable(self, name, attributes):
        """Create an element and insert it into the tree""" 
        element = self.elementClass(name)
        element.attributes = attributes
        if self.openElements[-1].name not in tableInsertModeElements:
            return self.insertElementNormal(name, attributes)
        else:
            #We should be in the InTable mode. This means we want to do
            #special magic element rearranging
            parent, insertBefore = self.getTableMisnestedNodePosition()
            if insertBefore is None:
                parent.appendChild(element)
            else:
                parent.insertBefore(element, insertBefore)
            self.openElements.append(element)
        return element

    def insertText(self, data, parent=None):
        """Insert text data."""
        if parent is None:
            parent = self.openElements[-1]

        if (not(self.insertFromTable) or (self.insertFromTable and
                                          self.openElements[-1].name not in
                                          tableInsertModeElements)):
            parent.insertText(data)
        else:
            #We should be in the InTable mode. This means we want to do
            #special magic element rearranging
            parent, insertBefore = self.getTableMisnestedNodePosition()
            parent.insertText(data, insertBefore)
            
    def getTableMisnestedNodePosition(self):
        """Get the foster parent element, and sibling to insert before
        (or None) when inserting a misnested table node"""
        #The foster parent element is the one which comes before the most
        #recently opened table element
        #XXX - this is really inelegant
        lastTable=None
        fosterParent = None
        insertBefore = None
        for elm in self.openElements[::-1]:
            if elm.name == u"table":
                lastTable = elm
                break
        if lastTable:
            #XXX - we should really check that this parent is actually a
            #node here
            if lastTable.parent:
                fosterParent = lastTable.parent
                insertBefore = lastTable
            else:
                fosterParent = self.openElements[
                    self.openElements.index(lastTable) - 1]
        else:
            assert self.innerHTML
            fosterParent = self.openElements[0]
        return fosterParent, insertBefore

    def generateImpliedEndTags(self, exclude=None):
        name = self.openElements[-1].name
        if (name in frozenset(("dd", "dt", "li", "p", "td", "th", "tr"))
            and name != exclude):
            self.openElements.pop()
            # XXX Until someone has broven that the above breaks stuff I think
            # we should keep it in.
            # self.processEndTag(name)
            self.generateImpliedEndTags(exclude)
