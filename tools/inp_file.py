import codecs
from collections import OrderedDict

from tools.network import Curve


class InpFile:

    def __init__(self):
        pass

    @staticmethod
    def read_patterns(inp_file_path):

        pattern_names_d = OrderedDict()
        patterns_d = OrderedDict()

        start_line = None
        end_line = None
        with codecs.open(inp_file_path, 'r', encoding='UTF-8') as inp_f:

            lines = inp_f.read().splitlines()
            patterns_started = False
            for l in range(len(lines)):
                if lines[l].upper().startswith('[PATTERNS]'):
                    patterns_started = True
                    start_line = l + 1
                    continue
                if lines[l].startswith('[') and patterns_started:
                    end_line = l - 1
                    break

        if end_line is None:
            end_line = len(lines)

        for l in range(start_line, end_line):
            if not lines[l].startswith(';'):
                words = lines[l].strip().replace('\t', ' ').split()
                if words[0] not in patterns_d:
                    pattern_names_d[words[0]] = lines[l-1][1:]
                if words[0] not in patterns_d:
                    patterns_d[words[0]] = []
                for w in range(1, len(words)):
                    patterns_d[words[0]].append(float(words[w]))

        return pattern_names_d, patterns_d

    @staticmethod
    def read_curvers(inp_file_path):
        start_line = None
        end_line = None
        with codecs.open(inp_file_path, 'r', encoding='UTF-8') as inp_f:

            lines = inp_f.read().splitlines()
            curves_started = False
            for l in range(len(lines)):
                if lines[l].upper().startswith('[CURVES]'):
                    curves_started = True
                    start_line = l + 1
                    continue
                if lines[l].startswith('[') and curves_started:
                    end_line = l - 1
                    break

        if end_line is None:
            end_line = len(lines)

        curves_d = {}

        for l in range(start_line, end_line):
            if not lines[l].strip().startswith(';'):
                words = lines[l].strip().replace('\t', ' ').split()
                if words[0] not in curves_d:
                    new_curve = Curve(lines[l-1][1:])
                    curves_d[words[0]] = new_curve
                    x = words[1]
                    y = words[2]
                    curves_d[words[0]].add_xy(x, y)
                    continue
                else:
                    x = words[1]
                    y = words[2]
                    curves_d[words[0]].add_xy(x, y)

        return curves_d

