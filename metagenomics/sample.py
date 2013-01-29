import sys
import collections
import os
import copy
import math

from metagenomics.filetypes import SffFile, FastqFile
from metagenomics.tools import Sff2Fastq, GetMID, Pagan, Uchime
from metagenomics.filters import Filter
from metagenomics.db import SequenceDB

class Sample(object) :
    def __init__(self, sff_fname, workingdir, mid_length, seqdb) :
        self.sff = SffFile(sff_fname)
        self.workingdir = workingdir
        self.fastq = Sff2Fastq().run(self.sff, self.workingdir)
        self.mid_length = mid_length
        self.db = seqdb
        self.seqcounts = collections.Counter()
        self.chimeras = []

    def preprocess(self, filt, compressed_length, mid_errors=1, ignore_first_homopolymer=False) :

        mid = GetMID(self.mid_length).run(self.fastq.get_filename())

        self.fastq.open()

        for seq in self.fastq :
            if filt.accept(seq) :
                # ensure there are not too many errors in the mid
                if self.__hamming_distance(mid, seq[:10]) > mid_errors :
                    continue

                # everything else assumes the mid does not exist
                seq.remove_mid()

                # if the last character of the mid is the same as the first character
                # of the read itself, there is a problem as the mid may end in a homopolymer
                # error, therefore we do two passes
                # during the second pass, the first homopolymer can be trimmed iff the resulting
                # sequence is already in the database, if this sequence is genuine (ie: not starting
                # with a homopolymer from the mid, then any more will be clustered with it anyway)
                if ignore_first_homopolymer :
                    if seq.compressed[1:compressed_length+1] in self.db :
                        seq.ltrim(seq[0])

                # the database can only handle sequences where the compressed representation of
                # that sequence are of identical length
                seq.ctruncate(compressed_length)

                self.seqcounts[self.db.put(seq)] += 1

        self.fastq.close()

    def simple_cluster(self, similarity) :
        threshold = math.ceil(self.__average_length() * (1.0 - similarity))
        clusters = []

        # perform multiple alignment
        fq = Pagan().get_454_alignment(self.print_sample_raw())
        fq.open()

        # cluster based on hamming distance
        for seq in fq :
            clustered = False

            if seq.id == ">consensus" :
                continue

            for cluster in clusters :
                hamming = self.__hamming_distance(cluster[0].sequence, seq.sequence)
                if hamming < threshold :
                    cluster.append(seq)
                    clustered = True
                    break

            if not clustered :
                clusters.append([seq])

        fq.close()

        # print out clusters
        f = open(self.workingdir + os.sep + self.sff.get_basename() + ".cluster", 'w')

        for i in range(len(clusters)) :
            for seq in clusters[i] :
                print >> f, "%s otu=%d %d" % (seq.id, i, self.__hamming_distance(clusters[1][0].sequence, seq.sequence))
                print >> f, seq.sequence

        f.close()

    def detect_chimeras(self) :
        self.chimeras = Uchime().run(self.print_sample_raw(duplicate_label="/ab"))

    def print_sample_raw(self, whitelist=None, duplicate_label=" NumDuplicates") :
        f = open(self.workingdir + os.sep + self.sff.get_basename() + ".sample", 'w')

        for key,freq in self.seqcounts.most_common() :
            if ((whitelist is None) or (key in whitelist)) and (key not in self.chimeras) :
                print >> f, ">seq%d%s=%d" % (key, duplicate_label, freq)
                print >> f, self.db.get(key).canonical.sequence

        f.close()

        return f.name

    def __hamming_distance(self, mid, seq) :
        return len(filter(lambda x: x[0] != x[1], zip(mid, seq)))

    def __average_length(self) :
        total_length = 0
        num_seq = 0

        for key,freq in self.seqcounts.iteritems() :
            total_length += (freq * len(self.db.get(key).canonical))
            num_seq += freq

        return total_length / num_seq

    def __merge(self, fromkey, tokey) :
        self.seqcounts[tokey] += self.seqcounts[fromkey]
        del self.seqcounts[fromkey]

    def __most_numerous_freq(self) :
        return self.seqcounts.most_common()[0][1] if len(self.seqcounts) != 0 else 0

    def __len__(self) :
        return sum(self.seqcounts.values())

    def __str__(self) :
        return "%s: %s (#seq=%d unique=%d mostfreq = %d)" % \
               (type(self).__name__, self.sff.get_basename(), len(self), len(self.seqcounts), self.__most_numerous_freq())

class NematodeSample(Sample) :
    def __init__(self, sff_fname, workingdir, mid_length, seqdb, metadata) :
        super(NematodeSample, self).__init__(sff_fname, workingdir, mid_length, seqdb)
        self.metadata = metadata

