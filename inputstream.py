import codecs

class HTMLInputStream(object):
    """ Provides a unicode stream of characters to the HTMLTokenizer.
    
    This class takes care of character encoding and removing or replacing
    incorrect byte-sequences and also provides column and line tracking.
    """
    
    def __init__(self, stream, encoding=None):
        """ Initialise the HTMLInputReader.
        
        The stream can either be a file-object, filename, url or string
        
        The optional encoding parameter must be a string that indicates
        the encoding.  If specified, that encoding will be used,
        regardless of any BOM or later declaration (such as in a meta
        element)
        """
        
        # Position Statistics
        self.line = 1
        self.col = 0
        
        # Encoding Information
        self.charEncoding = encoding
        
        # Original Stream
        self.stream = self.openStream(stream)
        
        # Try to detect the encoding of the stream by looking for a BOM
        encoding = self.detectEncoding()
        
        # Store whether we need to skip the BOM in future
        if encoding:
            self.skipBOM = True
        else:
            self.skipBOM = False
        
        # If an encoding was specified or detected from the BOM don't allow
        # the encoding to be changed futher into the stream
        if self.charEncoding or encoding:
            self.allowEncodingOverride = False
        else:
            self.allowEncodingOverride = True
        
        # If an encoding wasn't specified, use the encoding detected from the
        # BOM, if present, otherwise use the default encoding
        if not self.charEncoding:
            self.charEncoding = encoding or "cp1252"
        
        # Encoded file stream providing Unicode characters replacing characters
        # unable to be encoded with the Unicode replacement character
        self.encodedStream = codecs.EncodedFile(self.stream, self.charEncoding,
          errors='replace')
        
        self.seek(0)
    
    def openStream(self, stream):
        """ Opens stream first trying the native open function, if that
        fails try to open as a URL and finally treating stream as a string.
        
        Returns a file-like object.
        """
        # Already a file-like object?
        if hasattr(stream, 'seek'):
            return stream
        
        # Try opening stream normally
        try:
            return open(stream)
        except: pass
        
        # Otherwise treat stream as a string and covert to a file-like object
        import StringIO as StringIO
        return StringIO.StringIO(str(stream))
    
    def detectEncoding(self):
        """ Attempts to detect the character encoding of the stream.
        
        If an encoding can be determined from the BOM return the name of the
        encoding otherwise return None
        """
        
        bomDict = {
            codecs.BOM_UTF8: 'utf-8',
            codecs.BOM_UTF16_LE: 'utf-16-le', codecs.BOM_UTF16_BE: 'utf-16-be',
            codecs.BOM_UTF32_LE: 'utf-32-le', codecs.BOM_UTF32_BE: 'utf-32-be'
        }
        
        # Go to beginning of file and read in 4 bytes
        self.stream.seek(0)
        string = self.stream.read(4)
        
        # Try detecting the BOM using bytes from the string
        encoding = bomDict.get(string[:3])       # UTF-8
        if not encoding:
            encoding = bomDict.get(string[:2])   # UTF-16
            if not encoding:
                encoding = bomDict.get(string)   # UTF-32
        
        # Go back to the beginning of the file
        self.stream.seek(0)
        
        return encoding
    
    def declareEncoding(self, encoding):
        """Report the encoding declared by the meta element
        
        If the encoding is currently only guessed, then this
        will read subsequent characters in that encoding.
        
        If the encoding is not compatible with the guessed encoding
        and non-US-ASCII characters have been seen, parsing will
        have to begin again.
        """
        pass
    
    def read(self, size=1, stopAt=None):
        """ Read at most size characters from the stream stopping when
        encountering a character in stopAt if supplied.
        
        stopAt can be any iterable object such as a string, list or tuple.
        
        Returns a string from the stream with null bytes and new lines
        normalized
        """
        charStack = []
        
        while (len(charStack) < size) or stopAt:
            charStack.append(self.encodedStream.read(1))
            if charStack[-1] == u"\x00":
                charStack[-1] = u"\uFFFD"
            elif charStack[-1] == u"\r":
                if self.lookAhead(1) == u"\n":
                    charStack.pop()
                else:
                    charStack[-1] = u"\n"
            if stopAt and charStack and charStack[-1] in stopAt:
                break
        
        # Keep track of line and column count
        for c in charStack:
            if c == u"\n":
                self.line += 1
                self.col = 0
            else:
                self.col += 1
        
        # Return normalized stream
        return "".join(charStack)
    
    def seek(self, offset, whence=0):
        """ Proxy method for seeking withing the input stream.
        """
        
        # XXX TODO: Still need to find a way to track line and col after
        # seeking. Seeking back is easy but going forward will need reading
        # characters up to that point
        
        self.encodedStream.seek(offset, whence)
        # Skip over the BOM if needed
        if not self.tell() and self.skipBOM:
            self.encodedStream.read(1)
    
    def tell(self):
        """ Returns the streams current position
        """
        return self.encodedStream.tell()
    
    def readUntil(self, charList):
        """ Returns a string of characters from the stream until a character
        in charList is found or EOF is reached
        """
        return self.read(stopAt=charList)
    
    def lookAhead(self, amount):
        """ Returns the amount of characters specified without moving
        forward within the stream.
        """
        string = self.read(amount)
        self.seek(-len(string), 1)
        return string

if __name__ == "__main__":
    try:
        # Hard coded file name for now, this will need to be fixed later
        stream = HTMLInputStream("tests/utf-8-bom.html")
        
        char = stream.read(1)
        while char:
            print char
            char = stream.read(1)
        print "EOF"
    except IOError:
        print "The file does not exist."
