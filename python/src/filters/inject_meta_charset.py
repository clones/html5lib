import _base

class Filter(_base.Filter):
    def __init__(self, source, encoding):
        _base.Filter.__init__(self, source)
        self.encoding = encoding

    def __iter__(self):
        state = "pre_head"
        meta_found = (self.encoding is None)
        pending = []

        for token in _base.Filter.__iter__(self):
            type = token["type"]
            if type == "StartTag":
                if token["name"].lower() == "head":
                    state = "in_head"

            elif type == "EmptyTag":
                if token["name"].lower() == "meta":
                   # replace charset with actual encoding
                   for i,(name,value) in enumerate(token["data"]):
                       if name == 'charset':
                          token["data"][i] = (token["data"][i][0], self.encoding)
                          meta_found = True

                elif token["name"].lower() == "head" and not meta_found:
                    # insert meta into empty head
                    yield {"type": "StartTag", "name": "head",
                           "data": token["data"]}
                    yield {"type": "EmptyTag", "name": "meta",
                           "data": [["charset", self.encoding]]}
                    yield {"type": "EndTag", "name": "head"}
                    meta_found = True
                    continue

            elif type == "EndTag":
                if token["name"].lower() == "head" and pending:
                    # insert meta into head (if necessary) and flush pending queue
                    yield pending.pop(0)
                    if not meta_found:
                        yield {"type": "EmptyTag", "name": "meta",
                               "data": [["charset", self.encoding]]}
                    while pending:
                        yield pending.pop(0)
                    meta_found = True
                    state = "post_head"

            if state == "in_head":
                pending.append(token)
            else:
                yield token
