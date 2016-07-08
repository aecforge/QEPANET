import codecs

class Pattern:

    def __init__(self):
        pass

    @staticmethod
    def read_inp_file(inp_file_path):

        pattern_names_d = {}
        patterns_d = {}

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

        for l in range(start_line, end_line):
            if not lines[l].startswith(';'):
                words = lines[l].strip().replace('\t', ' ').split()
                if words[0] not in patterns_d:
                    pattern_names_d[words[0]] = lines[l-1][0:]
                if words[0] not in patterns_d:
                    patterns_d[words[0]] = []
                for w in range(1, len(words)):
                    patterns_d[words[0]].append(float(words[w]))

        print len(patterns_d)

Pattern.read_inp_file('C:/Users/deluca/Downloads/acquedotto (2).inp')