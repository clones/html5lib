try:
    from sets import ImmutableSet as frozenset
except:
    pass

from constants import contentModelFlags, spaceCharacters
from constants import entitiesWindows1252, entities, voidElements
from constants import asciiLowercase, asciiUppercase, asciiLetters
from constants import digits, hexDigits, EOF

from inputstream import HTMLInputStream

# Token objects used to hold token data when tokens are in the
# process of being constructed
class Token(object):
    """ Base class from which all tokens derive
    """
    def __init__(self, name=None, data=None):
        self.name = name
        self.data = data

    def __str__(self):
        return '%s: %s %s' % (self.__class__.__name__, self.name or '', self.data or '')

class Character(Token):
    """ Token representing a Character

    class Character(data)

    Creates a Character token with the given data attribute
    """
    def __init__(self, data):
        Token.__init__(self, None, data)

class Doctype(Token):
    """ Token representing a DOCTYPE

    class Doctype(name, data=True)

    Creates a DOCTYPE token with the given name and error state indicated by
    data. A doctype is marked in error if it's name in uppercase is not HTML
    """
    def __init__(self, name, data=True):
        Token.__init__(self, name, data)

class StartTag(Token):
    """ Token representing a Start Tag

    class StartTag(name, data=[])

    Creates a Start Tag with the given name and data as a list of (name, value)
    pairs representing attributes.
    """
    def __init__(self, name):
        Token.__init__(self, name)
        self.data = []

class EndTag(Token):
    """ Token representing an End Tag

    class EndTag(name, data=[])

    Creates an End Tag with the given name similiar to StartTag but listing
    attributes pairs in data will cause a ParseError Token to be sent along
    with it.
    """
    def __init__(self, name):
        Token.__init__(self, name)
        self.data = []

class Comment(Token):
    """ Token representing a Comment

    class Comment(data)

    Creates a Comment with a data attribute as given in the constructor.
    """
    def __init__(self, data=''):
        Token.__init__(self, None, data)

class ParseError(Token):
    """ Token representing a ParseError

    class ParseError()

    Creates a parse error for the parser to act on.
    """
    pass

class AtheistParseError(Token):
    """ Token representing an AtheistParseError
    """
    pass

class HTMLTokenizer(object):
    """ This class takes care of tokenizing HTML.

    * self.currentToken
      Holds the token that is currently being processed.

    * self.state
      Holds a reference to the method to be invoked... XXX

    * self.states
      Holds a mapping between states and methods that implement the state.

    * self.dataStream
    """

    # XXX need to fix documentation

    def __init__(self, stream):
        self.dataStream = HTMLInputStream(stream)

        self.states = {
            "data":self.dataState,
            "entityData":self.entityDataState,
            "tagOpen":self.tagOpenState,
            "closeTagOpen":self.closeTagOpenState,
            "tagName":self.tagNameState,
            "beforeAttributeName":self.beforeAttributeNameState,
            "attributeName":self.attributeNameState,
            "afterAttributeName":self.afterAttributeNameState,
            "beforeAttributeValue":self.beforeAttributeValueState,
            "attributeValueDoubleQuoted":self.attributeValueDoubleQuotedState,
            "attributeValueSingleQuoted":self.attributeValueSingleQuotedState,
            "attributeValueUnQuoted":self.attributeValueUnQuotedState,
            "bogusComment":self.bogusCommentState,
            "markupDeclarationOpen":self.markupDeclarationOpenState,
            "comment":self.commentState,
            "commentDash":self.commentDashState,
            "commentEnd":self.commentEndState,
            "doctype":self.doctypeState,
            "beforeDoctypeName":self.beforeDoctypeNameState,
            "doctypeName":self.doctypeNameState,
            "afterDoctypeName":self.afterDoctypeNameState,
            "bogusDoctype":self.bogusDoctypeState
        }

        # Setup the initial tokenizer state
        self.contentModelFlag = contentModelFlags['PCDATA']
        self.state = self.states['data']

        # The current token being created
        self.currentToken = None

        self.characterQueue = []
        self.tokenQueue = []

    def __iter__(self):
        """ This is where the magic happens.

        We do our usually processing through the states and when we have a token
        to return we yield the token which pauses processing until the next token
        is requested.
        """
        self.dataStream.reset()
        self.tokenQueue = []
        # Start processing. When EOF is reached self.state will return False
        # instead of True and the loop will terminate.
        while self.state():
            while self.tokenQueue:
                yield self.tokenQueue.pop(0)

    def changeState(self, state):
        self.state = self.states[state]

    def consumeChar(self):
        """Get the next character to be consumed

        If the characterQueue has characters they must be processed before any
        character is added to the stream. This is to allow e.g. lookahead
        """

        if self.characterQueue:
            return self.characterQueue.pop(0)
        else:
            return self.dataStream.readChar()

    def consumeCharsUntil(self, characters):
        """ Returns a string of characters from the stream up to but not
        including any character in characters or EOF. characters can be
        any container that supports the in method being called on it.
        """
        charStack = [self.consumeChar()]
        # Fill up from the local queue first
        while charStack[-1] and charStack[-1] not in characters and \
          self.characterQueue:
          charStack.append(self.characterQueue.pop(0))

        # Then direct from the dataStream
        while charStack[-1] and charStack[-1] not in characters:
            charStack.append(self.dataStream.readChar())

        # Put the character stopped on back to the front of the characterQueue
        # from where it came.
        self.characterQueue.insert(0, charStack.pop())
        return "".join(charStack)

    # Below are various helper functions the tokenizer states use worked out.

    def processSolidusInTag(self):
        """When a solidus (/) is encountered within a tag name what happens
        depends on whether the current tag name matches that of a void element.
        If it matches a void element atheists did the wrong thing and if it
        doesn't it's wrong for everyone.
        """

        # We need to consume another character to make sure it's a ">" before
        # throwing an atheist parse error.
        data = self.consumeChar()

        if self.currentToken.name in voidElements and data == u">":
            self.emitToken(AtheistParseError())
        else:
            self.emitToken(ParseError())

        # The character we just consumed need to be put back on the stack so it
        # doesn't get lost...
        self.characterQueue.append(data)

    def consumeNumberEntity(self, isHex):
        """This function returns either U+FFFD or the character based on the
        decimal or hexadecimal representation. It also discards ";" if present.
        If not present self.emitToken(ParseError()) is invoked.
        """

        allowed = digits
        radix = 10
        if isHex:
            allowed = hexDigits
            radix = 16

        char = u"\uFFFD"
        charStack = []

        # Consume all the characters that are in range while making sure we
        # don't hit an EOF.
        c = self.consumeChar()
        while c in allowed and c is not EOF:
            charStack.append(c)
            c = self.consumeChar()

        # Convert the set of characters consumed to an int.
        charAsInt = int("".join(charStack), radix)

        # If the integer is between 127 and 160 (so 128 and bigger and 159 and
        # smaller) we need to do the "windows trick".
        if 127 < charAsInt < 160:
            charAsInt = entitiesWindows1252[128 - charAsInt]

        # 0 is not a good number.
        if charAsInt == 0:
            charAsInt = 65533

        try:
            # XXX We should have a separate function that does "int" to
            # "unicodestring" conversion since this doesn't always work
            # according to hsivonen. Also, unichr has a limitation of 65535
            char = unichr(charAsInt)
        except:
            pass

        # Discard the ; if present. Otherwise, put it back on the queue and
        # invoke parseError on parser.
        if c != u";":
            self.emitToken(ParseError())
            self.characterQueue.append(c)

        return char

    def consumeEntity(self):
        char = None
        charStack = [self.consumeChar()]
        if charStack[0] == u"#":
            # We might have a number entity here.
            charStack.extend([self.consumeChar(), self.consumeChar()])
            if EOF in charStack:
                # If we reach the end of the file put everything up to EOF
                # back in the queue
                charStack = charStack[:charStack.index(EOF)]
                self.characterQueue.extend(charStack)
                self.emitToken(ParseError())
            else:
                if charStack[1].lower() == u"x" \
                  and charStack[2] in hexDigits:
                    # Hexadecimal entity detected.
                    self.characterQueue.append(charStack[2])
                    char = self.consumeNumberEntity(True)
                elif charStack[1] in digits:
                    # Decimal entity detected.
                    self.characterQueue.extend(charStack[1:])
                    char = self.consumeNumberEntity(False)
                else:
                    # No number entity detected.
                    self.characterQueue.extend(charStack)
                    self.emitToken(ParseError())
        # Break out if we reach the end of the file
        elif charStack[0] == EOF:
            self.emitToken(ParseError())
        else:
            # At this point in the process might have named entity. Entities
            # are stored in the global variable "entities".

            # Consume characters and compare to these to a substring of the
            # entity names in the list until the substring no longer matches.
            filteredEntityList = [e for e in entities if \
              e.startswith(charStack[0])]

            def entitiesStartingWith(name):
                return [e for e in filteredEntityList if e.startswith(name)]

            while (charStack[-1] != EOF and
                   entitiesStartingWith("".join(charStack))):
                charStack.append(self.consumeChar())

            # At this point we have a string that starts with some characters
            # that may match an entity
            entityName = None

            # Try to find the longest entity the string will match
            for entityLength in xrange(len(charStack)-1,1,-1):
                possibleEntityName = "".join(charStack[:entityLength])
                if possibleEntityName in entities:
                    entityName = possibleEntityName
                    break

            if entityName:
                char = entities[entityName]

                # Check whether or not the last character returned can be
                # discarded or needs to be put back.
                if not charStack[-1] == ";":
                    self.emitToken(ParseError())
                    self.characterQueue.extend(charStack[entityLength:])
            else:
                self.emitToken(ParseError())
                self.characterQueue.extend(charStack)
        return char

    def processEntityInAttribute(self):
        """This method replaces the need for "entityInAttributeValueState".
        """
        entity = self.consumeEntity()
        if entity:
            self.currentToken.data[-1][1] += entity
        else:
            self.currentToken.data[-1][1] += u"&"

    def emitCurrentToken(self):
        """This method is a generic handler for emitting the StartTag,
        EndTag, Comment and Doctype. It also sets the state to
        "data" because that's what's needed after a token has been emitted.
        """

        # Although isinstance() is http://www.canonical.org/~kragen/isinstance/
        # considered harmful it should be ok here given that the classes are for
        # internal usage.

        token = self.currentToken
        # For start tags convert attribute list into a distinct dictionary
        if isinstance(token, StartTag):
            # We need to remove the duplicate attributes and convert attributes
            # to a dict so that [["x", "y"], ["x", "z"]] becomes {"x": "y"}

            # AT When Python 2.4 is widespread we should use
            # dict(reversed(token.data))
            token.data = dict(token.data[::-1])
        # If an end tag has attributes it's a parse error and they should
        # be removed
        elif isinstance(token, EndTag) and token.data:
            self.emitToken(ParseError())
            token.data = {}

        # Add token to the queue to be yielded
        self.tokenQueue.append(token)

        self.changeState("data")

    def emitToken(self, token):
        """ Used to add tokens directly to the queue to be yeilded
        """
        self.tokenQueue.append(token)

    def emitCurrentTokenWithParseError(self, data=None):
        """This method is equivalent to emitCurrentToken (well, it invokes it)
        except that it also puts "data" back on the characters queue if a data
        argument is provided and it throws a parse error."""
        if data:
            self.characterQueue.append(data)
        self.emitCurrentToken()
        self.emitToken(ParseError())

    def attributeValueQuotedStateHandler(self, quoteType):
        data = self.consumeChar()
        if data == quoteType:
            self.changeState("beforeAttributeName")
        elif data == u"&":
            self.processEntityInAttribute()
        elif data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            data += self.consumeCharsUntil((quoteType, u"&"))
            self.currentToken.data[-1][1] += data

    # Below are the various tokenizer states worked out.

    # XXX AT Perhaps we should have Hixie run some evaluation on billions of
    # documents to figure out what the order of the various if and elif
    # statements should be.

    def dataState(self):
        data = self.consumeChar()
        if (data == u"&" and
          (self.contentModelFlag in
          (contentModelFlags["PCDATA"], contentModelFlags["RCDATA"]))):
            self.changeState("entityData")
        elif (data == u"<" and
          self.contentModelFlag != contentModelFlags["PLAINTEXT"]):
            self.changeState("tagOpen")
        elif data == EOF:
            # Tokenization ends.
            return False
        else:
            data += self.consumeCharsUntil((u"&", u"<"))
            for char in data:
                self.emitToken(Character(char))
        return True

    def entityDataState(self):
        assert self.contentModelFlag != contentModelFlags["CDATA"]

        entity = self.consumeEntity()
        if entity:
            self.emitToken(Character(entity))
        else:
            self.emitToken(Character(u"&"))
        self.changeState("data")
        return True

    def tagOpenState(self):
        data = self.consumeChar()
        if (self.contentModelFlag in
          (contentModelFlags["RCDATA"], contentModelFlags["CDATA"])):
            if data == u"/":
                self.changeState("closeTagOpen")
            else:
                self.emitToken(Character(u"<"))
                self.characterQueue.append(data)
                self.changeState("data")
        elif self.contentModelFlag == contentModelFlags['PCDATA']:
            if data == u"!":
                self.changeState("markupDeclarationOpen")
            elif data == u"/":
                self.changeState("closeTagOpen")
            elif data in asciiLetters:
                self.currentToken = StartTag(data.lower())
                self.changeState("tagName")
            elif data == u">":
                self.emitToken(ParseError())
                self.emitToken(Character(u"<"))
                self.emitToken(Character(u">"))
                self.changeState("data")
            elif data == u"?":
                self.emitToken(ParseError())
                self.characterQueue.append(data)
                self.changeState("bogusComment")
            else:
                self.emitToken(ParseError())
                self.emitToken(Character(u"<"))
                self.characterQueue.append(data)
                self.changeState("data")
        else:
            assert False
        return True

    def closeTagOpenState(self):
        if (self.contentModelFlag in
          (contentModelFlags["RCDATA"], contentModelFlags["CDATA"])):
            charStack = []

            # So far we know that "</" has been consumed. We now need to know
            # whether the next few characters match the name of last emitted
            # start tag which also happens to be the currentToken. We also need
            # to have the character directly after the characters that could
            # match the start tag name.
            for x in xrange(len(self.currentToken.name)+1):
                charStack.append(self.consumeChar())
                # Make sure we don't get hit by EOF
                if charStack[-1] == EOF:
                    break

            # Since this is just for checking. We put the characters back on
            # the stack.
            self.characterQueue.extend(charStack)

            if self.currentToken.name == "".join(charStack[:-1]).lower() \
              and charStack[-1] in (spaceCharacters |
              frozenset((u">", u"/", u"<", EOF))):
                # Because the characters are correct we can safely switch to
                # PCDATA mode now. This also means we don't have to do it when
                # emitting the end tag token.
                self.contentModelFlag = contentModelFlags["PCDATA"]
            else:
                self.emitToken(ParseError())
                self.emitToken(Character(u"<"))
                self.emitToken(Character(u"/"))
                self.changeState("data")

                # Need to return here since we don't want the rest of the
                # method to be walked through.
                return True

        if self.contentModelFlag == contentModelFlags["PCDATA"]:
            data = self.consumeChar()
            if data in asciiLetters:
                self.currentToken = EndTag(data.lower())
                self.changeState("tagName")
            elif data == u">":
                self.emitToken(ParseError())
                self.changeState("data")
            elif data == EOF:
                self.emitToken(ParseError())
                self.emitToken(Character(u"<"))
                self.emitToken(Character(u"/"))
                self.characterQueue.append(data)
                self.changeState("data")
            else:
                self.emitToken(ParseError())
                self.characterQueue.append(data)
                self.changeState("bogusComment")
        return True

    def tagNameState(self):
        data = self.consumeChar()
        if data in spaceCharacters:
            self.changeState("beforeAttributeName")
        elif data == u">":
            self.emitCurrentToken()
        elif data in asciiUppercase:
            self.currentToken.name += data.lower()
        elif data == u"<" or data == EOF:
            self.emitCurrentTokenWithParseError(data)
        elif data == u"/":
            self.processSolidusInTag()
            self.changeState("beforeAttributeName")
        else:
            self.currentToken.name += data
        return True

    def beforeAttributeNameState(self):
        data = self.consumeChar()
        if data in spaceCharacters:
            pass
        elif data == u">":
            self.emitCurrentToken()
        elif data in asciiUppercase:
            self.currentToken.data.append([data.lower(), ""])
            self.changeState("attributeName")
        elif data == u"/":
            self.processSolidusInTag()
        elif data == u"<" or data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken.data.append([data, ""])
            self.changeState("attributeName")
        return True

    def attributeNameState(self):
        data = self.consumeChar()
        leavingThisState = True
        if data in spaceCharacters:
            self.changeState("afterAttributeName")
        elif data == u"=":
            self.changeState("beforeAttributeValue")
        elif data == u">":
            # XXX If we emit here the attributes are converted to a dict
            # without being checked and when the code below runs we error
            # because data is a dict not a list
            pass
        elif data in asciiUppercase:
            self.currentToken.data[-1][0] += data.lower()
            leavingThisState = False
        elif data == u"/":
            self.processSolidusInTag()
            self.changeState("beforeAttributeName")
        elif data == u"<" or data == EOF:
            self.emitCurrentTokenWithParseError(data)
            leavingThisState = False
        else:
            self.currentToken.data[-1][0] += data
            leavingThisState = False

        if leavingThisState:
            # Attributes are not dropped at this stage. That happens when the
            # start tag token is emitted so values can still be safely appended
            # to attributes, but we do want to report the parse error in time.
            for name, value in self.currentToken.data[:-1]:
                if self.currentToken.data[-1][0] == name:
                    self.emitToken(ParseError())
            # XXX Fix for above XXX
            if data == u">":
                self.emitCurrentToken()
        return True

    def afterAttributeNameState(self):
        data = self.consumeChar()
        if data in spaceCharacters:
            pass
        elif data == u"=":
            self.changeState("beforeAttributeValue")
        elif data == u">":
            self.emitCurrentToken()
        elif data in asciiUppercase:
            self.currentToken.data.append([data.lower(), ""])
            self.changeState("attributeName")
        elif data == u"/":
            self.processSolidusInTag()
            self.changeState("beforeAttributeName")
        elif data == u"<" or data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken.data.append([data, ""])
            self.changeState("attributeName")
        return True

    def beforeAttributeValueState(self):
        data = self.consumeChar()
        if data in spaceCharacters:
            pass
        elif data == u"\"":
            self.changeState("attributeValueDoubleQuoted")
        elif data == u"&":
            self.changeState("attributeValueUnQuoted")
            self.characterQueue.append(data);
        elif data == u"'":
            self.changeState("attributeValueSingleQuoted")
        elif data == u">":
            self.emitCurrentToken()
        elif data == u"<" or data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken.data[-1][1] += data
            self.changeState("attributeValueUnQuoted")
        return True

    def attributeValueDoubleQuotedState(self):
        # AT We could also let self.attributeValueQuotedStateHandler always
        # return true and then return that directly here. Not sure what is
        # faster or better...
        self.attributeValueQuotedStateHandler(u"\"")
        return True

    def attributeValueSingleQuotedState(self):
        self.attributeValueQuotedStateHandler(u"'")
        return True

    def attributeValueUnQuotedState(self):
        data = self.consumeChar()
        if data in spaceCharacters:
            self.changeState("beforeAttributeName")
        elif data == u"&":
            self.processEntityInAttribute()
        elif data == u">":
            self.emitCurrentToken()
        elif data == u"<" or data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken.data[-1][1] += data
        return True

    def bogusCommentState(self):
        assert self.contentModelFlag == contentModelFlags["PCDATA"]

        charStack = self.consumeCharsUntil((u">"))

        char = self.consumeChar()

        if char == EOF:
            self.characterQueue.append(EOF)

        # Make a new comment token and give it as value the characters the loop
        # consumed. The last character is either > or EOF and should not be
        # part of the comment data.
        self.currentToken = Comment("".join(charStack))
        self.emitCurrentToken()
        return True

    def markupDeclarationOpenState(self):
        assert self.contentModelFlag == contentModelFlags["PCDATA"]

        charStack = [self.consumeChar(), self.consumeChar()]
        if charStack == [u"-", u"-"]:
            self.currentToken = Comment()
            self.changeState("comment")
        else:
            for x in xrange(5):
                charStack.append(self.consumeChar())
            #XXX - put in explicit None check
            if (not EOF in charStack and
                "".join(charStack).upper() == u"DOCTYPE"):
                self.changeState("doctype")
            else:
                self.emitToken(ParseError())
                self.characterQueue.extend(charStack)
                self.changeState("bogusComment")
        return True

    def commentState(self):
        data = self.consumeChar()
        if data == u"-":
            self.changeState("commentDash")
        elif data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken.data += data+self.consumeCharsUntil(u"-")
        return True

    def commentDashState(self):
        data = self.consumeChar()
        if data == u"-":
            self.changeState("commentEnd")
        elif data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken.data += u"-" + data
            self.changeState("comment")
        return True

    def commentEndState(self):
        data = self.consumeChar()
        if data == u">":
            self.emitCurrentToken()
        elif data == u"-":
            self.emitToken(ParseError())
            self.currentToken.data += data
        elif data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.emitToken(ParseError())
            self.currentToken.data += u"--" + data
            self.changeState("comment")
        return True

    def doctypeState(self):
        data = self.consumeChar()
        if data in spaceCharacters:
            self.changeState("beforeDoctypeName")
        else:
            self.emitToken(ParseError())
            self.characterQueue.append(data)
            self.changeState("beforeDoctypeName")
        return True

    def beforeDoctypeNameState(self):
        data = self.consumeChar()
        if data in spaceCharacters:
            pass
        elif data in asciiLowercase:
            self.currentToken = Doctype(data.upper())
            self.changeState("doctypeName")
        elif data == u">":
            # Character needs to be consumed per the specification so don't
            # invoke emitCurrentTokenWithParseError with "data" as argument.
            self.emitCurrentTokenWithParseError()
        elif data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken = Doctype(data)
            self.changeState("doctypeName")
        return True

    def doctypeNameState(self):
        data = self.consumeChar()
        needsDoctypeCheck = False
        if data in spaceCharacters:
            self.changeState("afterDoctypeName")
            needsDoctypeCheck = True
        elif data == u">":
            self.emitCurrentToken()
        elif data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            # We can't just uppercase everything that arrives here. For
            # instance, non-ASCII characters.
            if data in asciiLowercase:
                data = data.upper()
            self.currentToken.name += data
            needsDoctypeCheck = True

        # After some iterations through this state it should eventually say
        # "HTML". Otherwise there's an error.
        if needsDoctypeCheck and self.currentToken.name == u"HTML":
            self.currentToken.data = False
        return True

    def afterDoctypeNameState(self):
        data = self.consumeChar()
        if data in spaceCharacters:
            pass
        elif data == u">":
            self.emitCurrentToken()
        elif data == EOF:
            self.currentToken.data = True
            self.emitCurrentTokenWithParseError(data)
        else:
            self.emitToken(ParseError())
            self.currentToken.data = True
            self.changeState("bogusDoctype")
        return True

    def bogusDoctypeState(self):
        data = self.consumeChar()
        if data == u">":
            self.emitCurrentToken()
        elif data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            pass
        return True
