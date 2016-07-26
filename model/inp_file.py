import codecs

from network import Title, Junction, Reservoir, Tank, Pipe, Pump, Valve
from system_ops import Curve, Pattern
from ..tools.parameters import Parameters


class InpFile:

    def __init__(self):
        pass

    @staticmethod
    def read_patterns(inp_file_path):

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

        patterns_d = {}

        for l in range(start_line, end_line):
            if not lines[l].startswith(';'):
                words = lines[l].strip().replace('\t', ' ').split()
                if words[0] not in patterns_d:
                    patterns_d[words[0]] = Pattern(lines[l-1][1:], words[0])
                    for w in range(1, len(words)):
                        patterns_d[words[0]].add_value(words[w])
                    continue
                else:
                    for w in range(1, len(words)):
                        patterns_d[words[0]].add_value(words[w])

        return patterns_d

    @staticmethod
    def read_curves(inp_file_path):

        start_line = None
        end_line = None
        with codecs.open(inp_file_path, 'r', encoding='UTF-8') as inp_f:

            lines = inp_f.read().splitlines()
            for l in range(len(lines)):
                lines[l] = lines[l].strip()

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
            if not lines[l].startswith(';'):
                words = lines[l].replace('\t', ' ').split()
                if words[0] not in curves_d:
                    curves_d[words[0]] = Curve(lines[l-1][1:], words[0])
                    x = words[1]
                    y = words[2]
                    curves_d[words[0]].add_xy(x, y)
                    continue
                else:
                    x = words[1]
                    y = words[2]
                    curves_d[words[0]].add_xy(x, y)

        return curves_d

    @staticmethod
    def write_inp_file(inp_file_path, title):

        out = []

        with codecs.open(inp_file_path, 'w', encoding='UTF-8') as inp_f:

            # Title
            if title is not None:
                out.append(InpFile.build_section_keyword(Title.section_name))
                out.extend(InpFile.split_line(title))

            # Junctions
            out.append(InpFile.build_section_keyword(Junction.section_name))
            out.append(Junction.section_header)
            out.append(InpFile.build_dashline(Junction.section_header))

            f_fts = Parameters.junctions_vlay.getFeatures()


    @staticmethod
    def split_line(line, n=255):
        lines = [line[i:i + n] for i in range(0, len(line), n)]
        return lines

    @staticmethod
    def build_section_keyword(section_name):
        return '[' + section_name + ']'

    @staticmethod
    def build_comment(comment):
        comments = InpFile.split_line(comment)
        for c in range(comments):
            comments[c] = '; ' + comments[c]
        return comments

    @staticmethod
    def build_dashline(text):
        dashline = ''
        for d in range(len(text)):
            dashline += '-'
        return dashline




