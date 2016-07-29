import codecs

from network import Title, Junction, Reservoir, Tank, Pipe, Pump, Valve
from system_ops import Curve, Pattern
import math
from ..tools.parameters import Parameters


class InpFile:

    def __init__(self):
        pass

    @staticmethod
    def write_patterns(parameters, inp_file_path):

        # Rewrite whole file
        with codecs.open(inp_file_path, 'w', encoding='UTF-8') as inp_f:
            InpFile.write_lines(inp_f, InpFile.build_section_keyword(Pattern.section_name))
            InpFile.write_lines(inp_f, InpFile.build_comment(Pattern.section_header))

            for pattern in parameters.patterns:
                if pattern.desc is not None:
                    InpFile.write_lines(inp_f, InpFile.build_comment(pattern.desc))
                InpFile.write_lines(inp_f, InpFile.from_values_to_lines(pattern.values, line_header=pattern.id, vals_per_line=6))

    @staticmethod
    def write_lines(inp_file, lines):

        if type(lines) is str:
            inp_file.write(lines + '\n')
        else:
            for line in lines:
                inp_file.write(line + '\n')

    @staticmethod
    def read_patterns(parameters, inp_file_path):

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

        if start_line is None:
            return []

        if end_line is None:
            end_line = len(lines)

        patterns_d = {}

        for l in range(start_line, end_line):
            if not lines[l].startswith(';'):
                words = lines[l].strip().replace('\t', ' ').split()
                if words[0] not in patterns_d:
                    patterns_d[words[0]] = Pattern(words[0], lines[l-1][1:])
                    for w in range(1, len(words)):
                        patterns_d[words[0]].add_value(float(words[w]))
                    continue
                else:
                    for w in range(1, len(words)):
                        patterns_d[words[0]].add_value(float(words[w]))

        parameters.patterns = patterns_d.values()

        # Update GUI


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

        return curves_d.values()

    @staticmethod
    def write_inp_file(parameters, inp_file_path, title):

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

            f_fts = parameters.junctions_vlay.getFeatures()

    @staticmethod
    def split_line(line, n=255):
        lines = [line[i:i + n] for i in range(0, len(line), n)]
        return lines

    @staticmethod
    def from_values_to_lines(values, decimal_places=2, n=255, element_size=10, line_header=None, vals_per_line=None):

        if line_header is not None:
            header = str(InpFile.pad(line_header, element_size))
        else:
            header = ''

        svalues = []
        for value in values:
            formatter = '{0:.' + str(decimal_places) + 'f}'
            svalue = formatter.format(value)
            svalue = InpFile.pad(svalue, element_size)
            svalues.append(svalue)

        # Calc elements per line
        if vals_per_line is None:
            vals_per_line = int(math.floor((n - len(header)) / (element_size + 1)))

        lines_nr = int(math.ceil(len(svalues) / vals_per_line))

        lines = []
        v = 0
        for l in range(lines_nr):
            line = header
            for vpl in range(vals_per_line):
                line += svalues[v]
                v += 1
            lines.append(line)

        return lines

    @staticmethod
    def pad(text, blanks_nr):
        for t in range(blanks_nr - len(text)):
            text += ' '
        text += '\t'
        return text

    @staticmethod
    def build_section_keyword(section_name):
        return '[' + section_name + ']'

    @staticmethod
    def build_comment(comment):
        comments = InpFile.split_line(comment)
        for c in range(len(comments)):
            comments[c] = ';' + comments[c]
        return comments

    @staticmethod
    def build_dashline(text):
        dashline = ''
        for d in range(len(text)):
            dashline += '-'
        return dashline