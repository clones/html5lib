import codecs

def openSource(source):
    """ Opens source first trying to open a local file, if that fails 
    try to open as a URL and finally treating source as a string.
    
    Returns a file-like object.
    """
    # Already a file-like object?
    if hasattr(source, 'tell'):
        return source

    # Try opening source normally
    try:
        return open(source)
    except: pass

    # Try opening source as a URL and storing the bytes returned so
    # they can be turned into a file-like object below
    try:
        import urllib
        source = urllib.urlopen(source).read(-1)
    except: pass

    # Treat source as a string and make it into a file-like object
    import cStringIO as StringIO
    return StringIO.StringIO(str(source))

class HTMLInputStream(object):
    """For reading data from an input stream

    This deals with character encoding issues automatically.

    This keeps track of the current line and column number in the file
    automatically, as you consume and unconsume characters.
    """

    def __init__(self, source, encoding = None):
        """ Initialise the HTMLInputReader.

        The file parameter must be a File object.

        The optional encoding parameter must be a string that indicates
        the encoding.  If specified, that encoding will be used,
        regardless of any BOM or later declaration (such as in a meta
        element)
        """

        self.line = 1 # Current line number
        self.col = 0  # Current column number
        self.lineBreaks = [0]

        # Keep a reference to the unencoded file object so that a new
        # EncodedFile can be created later if the encoding is declared
        # in a meta element
        self.file = openSource(source)

        skipBOM = False
        self.charEncoding = self.detectBOM(self.file)
        if self.charEncoding:
            # The encoding is known from the BOM, don't allow later
            # declarations from the meta element to override this.
            skipBOM = True
            self.allowEncodingOverride = False
        else:
            # Using the default encoding, don't allow later
            # declarations from the meta element to override this.
            self.allowEncodingOverride = True
            self.charEncoding = "cp1252" # default to Windows-1252

        self.encodedFile = codecs.EncodedFile(self.file, self.charEncoding)
        if skipBOM:
            self.encodedFile.read(1)

    def detectBOM(self, fp):
        """ Attempts to detect the character encoding of the html file
        given by a file object fp. fp must not be a codec wrapped file
        object!

        The return value can be:
            - if detection of the BOM succeeds, the codec name of the
              corresponding unicode charset is returned

            - if BOM detection fails, None is returned.
        """
        # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/363841

        ### detection using BOM
        
        ## the BOMs we know, by their pattern
        bomDict = { # bytepattern : name              
                   (0x00, 0x00, 0xFE, 0xFF) : "utf_32_be",        
                   (0xFF, 0xFE, 0x00, 0x00) : "utf_32_le",
                   (0xFE, 0xFF, None, None) : "utf_16_be", 
                   (0xFF, 0xFE, None, None) : "utf_16_le", 
                   (0xEF, 0xBB, 0xBF, None) : "utf_8",
                  }

        ## go to beginning of file and get the first 4 bytes
        oldFP = fp.tell()
        fp.seek(0)
        (byte1, byte2, byte3, byte4) = tuple(map(ord, fp.read(4)))

        ## try bom detection using 4 bytes, 3 bytes, or 2 bytes
        bomDetection = bomDict.get((byte1, byte2, byte3, byte4))
        if not bomDetection :
            bomDetection = bomDict.get((byte1, byte2, byte3, None))
            if not bomDetection :
                bomDetection = bomDict.get((byte1, byte2, None, None))
        
        ## if BOM detected, we're done :-)
        fp.seek(0) # No BOM, return to the beginning of the file
        if bomDetection :
            return bomDetection
        return None

    def consumeChar(self):
        char = unicode(self.encodedFile.read(1), self.charEncoding)
        if char == "\n":
            # Move to next line and reset column count
            self.line += 1
            self.col = 0
            self.lineBreaks.append(self.encodedFile.tell())
        else:
            # Just increment the column counter
            self.col += 1
        return char or None

    def unconsumeChar(self):
        """Unconsume the previous character by seeking backwards thorough
        the file.
        """
        self.encodedFile.seek(-1, 1)
        if self.encodedFile.tell()+1 == self.lineBreaks[-1]:
            self.line -= 1
            self.lineBreaks.pop()
            self.col = self.encodedFile.tell()-self.lineBreaks[-1]
        else:
            self.col -= 1

    def declareEncoding(self, encoding):
        """Report the encoding declared by the meta element
        
        If the encoding is currently only guessed, then this
        will read subsequent characters in that encoding.

        If the encoding is not compatible with the guessed encoding
        and non-US-ASCII characters have been seen, parsing will
        have to begin again.
        """
        pass

if __name__ == "__main__":
    try:
        # Hard coded file name for now, this will need to be fixed later
        htmlFile = open("tests/utf-8-bom.html", "rU")
        stream = HTMLInputStream(htmlFile)

        char = stream.consumeChar()
        while char:
            line = stream.line
            col = stream.col
            if char == "\n":
                print "LF (%d, %d)" % (line, col)
            else:
                print "%s (%d, %d)" % (char, line, col)
            char = stream.consumeChar()
        print "EOF"
        htmlFile.close()
    except IOError:
        print "The file does not exist."
