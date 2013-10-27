class CodegenHelper:
    def __init__(self, f, tab = "    ", encoding = "ascii"):
        self._f = f
        self._encoding = encoding
        self._tab = tab.encode(encoding)

        self._stack = []
        self._last_line = ""

    def indent(self):
        self._stack.append(self._tab)

    def align(self):
        """ Allign following lines with the previous one. """
        self._stack.append(b' ' * len(self._last_line))

    def dedent(self):
        try:
            self._stack.pop()
        except IndexError:
            raise RuntimeError("Unbalanced indent/dedent.")

    def open_brace(self, brace = "{{"):
        self(brace);
        self.indent()

    def close_brace(self, brace = "}}"):
        self.dedent()
        self(brace)

    def __call__(self, text = "", *args, **kwargs):
        if len(text):
            self._f.write(b''.join(self._stack))
            self._last_line = self._format(text, *args, **kwargs)
            self._f.write(self._last_line)
        self._f.write(self._format("\n"))

    def _format(self, text, *args, **kwargs):
        return text.format(*args, **kwargs).encode(self._encoding)
