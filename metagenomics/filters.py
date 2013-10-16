import sys
import abc
import operator

class FilterError(Exception) :
    pass

class Filter(object) :
    __metaclass__ = abc.ABCMeta
    
    def __init__(self) :
        pass

    @abc.abstractmethod
    def accept(self, seq) :
        pass

class NullFilter(object) :
    def accept(self) :
        return True

class MultiFilter(Filter) :
    def __init__(self) :
        self.filters = []
        self.counts = []

    def add(self, f) :
        self.filters.append(f)
        self.counts.append(0)

    def accept(self, seq) :
        for index,f in enumerate(self.filters) :
            if not f.accept(seq) :
                self.count[index] += 1
                return False
        return True

    def reset(self) :
        for i in range(len(self.counts)) :
            self.counts[i] = 0

    def __len__(self) :
        return len(self.filters)

    def __str__(self) :
        s = ""
        for index,f in enumerate(self.filters) :
            s += "%s %d\n" % (f.__class__.__name__, self.counts[index])
        return s

class LengthFilter(Filter) :
    def __init__(self, length) :
        if length < 0 :
            raise FilterError, "%s: length is negative (%d)" % (type(self).__name__, length)

        self.length = length

    def accept(self, seq) :
        return len(seq) > self.length

class CompressedLengthFilter(LengthFilter) :
    def __init__(self, length) :
        super(CompressedLengthFilter, self).__init__(length) 

    def accept(self, seq) :
        if len(seq.compressed) < self.length :
            return False

        #seq.ctruncate(self.length)
        return True

class AmbiguousFilter(Filter) :
    def accept(self, seq) :
        return 'N' not in seq

class AverageQualityFilter(Filter) :
    def __init__(self, qual) :
        self.qual = qual

    def accept(self, seq) :
        tmp = seq.qualities
        return (sum(tmp) / float(len(tmp))) >= self.qual

class WindowedQualityFilter(Filter) :
    def __init__(self, qual, winlen) :
        self.qual = qual
        self.winlen = winlen

    def accept(self, seq) :
        if len(seq) < self.winlen :
            return False

        qual = seq.qualities
        qualsum = sum(qual[:self.winlen])
        total = self.qual * self.winlen

        for i in range(len(seq) - self.winlen) :
            if i != 0 :
                qualsum = qualsum - qual[i-1] + qual[i + self.winlen - 1]

            if qualsum < total :
                return False

        return True

class HomopolymerFilter(Filter) :
    def __init__(self, maxlen) :
        self.maxlen = maxlen

    def accept(self, seq) :
        tmpchar = ""
        tmphp = 0

        for c in seq.sequence :
            if c != tmpchar :
                tmpchar = c
                tmphp = 0

            tmphp += 1

            if tmphp > self.maxlen :
                return False

        return True

class MIDHomopolymer(Filter) :
    def __init__(self, reject=True) :
        self.op = operator.ne if reject else operator.eq

    def accept(self, seq) :
        return self.op(seq[9], seq[10])

