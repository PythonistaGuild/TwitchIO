

class StringParser:
    def __init__(self):
        self.count = 0
        self.index = 0
        self.eof = 0
        self.start = 0
        self.words = {}
        self.ignore = False

    def process_string(self, msg: str):

        while True:
            try:
                loc = msg[self.count]
            except IndexError:
                self.eof = self.count
                word = msg[self.start:self.eof]
                if not word:
                    break
                self.words[self.index] = msg[self.start:self.eof]
                break

            if loc.isspace() and not self.ignore:
                self.words[self.index] = msg[self.start:self.count]
                self.index += 1
                self.start = self.count + 1

            elif loc == '"':
                if not self.ignore:
                    self.start = self.count + 1
                    self.ignore = True
                else:
                    self.words[self.index] = msg[self.start:self.count]
                    self.index += 1
                    self.count += 1
                    self.start = self.count
                    self.ignore = False

            self.count += 1

        return self.words
