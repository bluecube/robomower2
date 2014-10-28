class HaltonSequence:
    """ Iterator over n-dimensional halton sequence """
    primes = [2, 3, 5, 7, 11, 13, 17]

    def __init__(self, dimension):
        if dimension < 1 or dimension > len(self.primes):
            raise ValueError("Dimension must be between 1 and " + str(len(self.primes)))
        self._dimension = dimension
        self._i = 0

    def __iter__(self):
        return self

    def __next__(self):
        self._i += 1

        ret = []
        for prime in self.primes[:self._dimension]:
            # This takes the number i in a number base prime and reverses the digits
            # and decimal dot.
            # Mostly copied from wikipedia

            i = self._i
            value = 0
            factor = 1
            while i > 0:
                factor /= prime
                value += factor * (i % prime)
                i //= prime

            ret.append(value)

        return ret
