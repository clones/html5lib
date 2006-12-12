try:
    from sets import ImmutableSet as frozenset
except:
    pass

class MethodDispatcher(dict):
    """Dict with 2 special properties:

    On initiation, keys that are lists, sets or tuples are converted to
    multiple keys so accessing any one of the items in the original
    list-like object returns the matching value

    md = MethodDispatcher({["foo", "bar"]:"baz"})
    md["foo"] == "baz"

    A default value which can be set through the setDefaultValue method
    """

    def __init__(self, items=()):
        _dictEntries = []
        for name,value in items:
            if type(name) in (list, tuple, frozenset, set):
                for item in name:
                    _dictEntries.append((item, value))
            else:
                _dictEntries.append((name, value))
        dict.__init__(self, _dictEntries)

    def setDefaultValue(self, value):
        # XXX I think we should not use a method here... it only complicates
        # things. I think we should use self.default instead. Short and simple.
        self.defaultValue = value

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            if hasattr(self, "defaultValue"):
                return self.defaultValue
            else:
                raise
