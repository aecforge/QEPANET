import codecs

from network import Title, Junction, Reservoir, Tank, Pipe, Pump, Valve
from system_ops import Curve, Pattern
import math
from ..model.network_handling import NetworkUtils
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
            parameters.patterns = []
            return

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
            InpFile._append_junctions(parameters, out)

            # Reservoirs
            InpFile._append_reservoirs(parameters, out)

            # Tanks
            InpFile._append_tanks(parameters, out)

            # Pipes
            InpFile._append_pipes(parameters, out)

            # Pumps
            InpFile._append_pumps(parameters, out)

            # Valves
            InpFile._append_valves(parameters, out)

    @staticmethod
    def _append_junctions(parameters, out):

        out.append(InpFile.build_section_keyword(Junction.section_name))
        out.append(Junction.section_header)
        out.append(InpFile.build_dashline(Junction.section_header))

        j_fts = parameters.junctions_vlay.getFeatures()
        for j_ft in j_fts:
            eid = j_ft.attribute(Junction.field_eid)
            demand = j_ft.attribute(Junction.field_name_demand)
            elev = j_ft.attribute(Junction.field_name_elevation)
            elev_corr = j_ft.attribute(Junction.field_name_elev_corr)
            pattern = j_ft.attribute(Junction.field_name_pattern)

            if elev_corr is None:
                elev_corr = 0

            elev += elev_corr

            line = InpFile.pad(eid)
            line += InpFile.pad('{0:.2f}'.format(elev))
            if demand is not None:
                line += InpFile.pad('{0:.5f}'.format(demand))
            else:
                line += InpFile.pad('')

            if pattern is not None:
                line += InpFile.pad(pattern)
            else:
                line += InpFile.pad('')

            out.append(line)

    @staticmethod
    def _append_reservoirs(parameters, out):

        out.append(InpFile.build_section_keyword(Reservoir.section_name))
        out.append(Reservoir.section_header)
        out.append(InpFile.build_dashline(Reservoir.section_header))

        r_fts = parameters.reservoirs_vlay.getFeatures()
        for r_ft in r_fts:
            eid = r_ft.attribute(Reservoir.field_name_eid)
            elev = r_ft.attribute(Reservoir.field_name_elevation)
            elev_corr = r_ft.attribute(Reservoir.field_name_elev_corr)
            head = r_ft.attribute(Reservoir.field_name_head)
            pattern = r_ft.attribute(Reservoir.field_name_pattern)

            if elev is None:
                elev = 0
            if elev_corr is None:
                elev_corr = 0

            head += elev + elev_corr

            # Line
            line = InpFile.pad(eid)
            line += InpFile.pad('{0:.2f}'.format(head))
            line += InpFile.pad(pattern)

            out.append(line)

    @staticmethod
    def _append_tanks(parameters, out):

        out.append(InpFile.build_section_keyword(Tank.section_name))
        out.append(Tank.section_header)
        out.append(InpFile.build_dashline(Tank.section_header))

        t_fts = parameters.tanks_vlay.getFeatures()
        for t_ft in t_fts:
            eid = t_ft.attribute(Tank.field_name_eid)
            curve = t_ft.attribute(Tank.field_name_curve)
            diameter = t_ft.attribute(Tank.field_name_diameter)
            elev = t_ft.attribute(Tank.field_name_elevation)
            elev_corr = t_ft.attribute(Tank.field_name_elev_corr)
            level_init = t_ft.attribute(Tank.field_name_level_init)
            level_max = t_ft.attribute(Tank.field_name_level_max)
            level_min = t_ft.attribute(Tank.field_name_level_min)
            vol_min = t_ft.attribute(Tank.field_name_vol_min)

            if elev_corr is None:
                elev_corr = 0

            elev += elev_corr

            # Line
            line = InpFile.pad(eid)
            line += InpFile.pad('{0:.2f}'.format(elev))
            line += InpFile.pad('{0:.4f}'.format(level_init))
            line += InpFile.pad('{0:.4f}'.format(level_min))
            line += InpFile.pad('{0:.4f}'.format(level_max))
            line += InpFile.pad('{0:.1f}'.format(diameter))
            line += InpFile.pad('{0:.4f}'.format(vol_min))
            if curve is not None:
                line += InpFile.pad(curve)

            out.append(line)

    @staticmethod
    def _append_pipes(parameters, out):

        out.append(InpFile.build_section_keyword(Pipe.section_name))
        out.append(Pipe.section_header)
        out.append(InpFile.build_dashline(Pipe.section_header))

        p_fts = parameters.pipes_vlay.getFeatures()
        for p_ft in p_fts:
            eid = p_ft.attribute(Pipe.field_name_eid)

            # Find start/end nodes
            adj_nodes = NetworkUtils.find_start_end_nodes(parameters, p_ft.geometry())
            start_node_id = adj_nodes[0].attribute(Junction.field_name_eid)
            end_node_id = adj_nodes[1].attribute(Junction.field_name_eid)

            length = p_ft.attribute(Pipe.field_name_length)
            diameter = p_ft.attribute(Pipe.field_name_diameter)
            roughness = p_ft.attribute(Pipe.field_name_roughness)
            minor_loss = p_ft.attribute(Pipe.field_name_minor_loss)
            status = p_ft.attribute(Pipe.field_name_status)

            # Line
            line = InpFile.pad(eid)
            line += InpFile.pad(start_node_id)
            line += InpFile.pad(end_node_id)
            line += InpFile.pad('{0:.2f}'.format(length))
            line += InpFile.pad('{0:.2f}'.format(diameter))
            line += InpFile.pad('{0:.2f}'.format(roughness))
            line += InpFile.pad('{0:.2f}'.format(minor_loss))
            line += InpFile.pad(status)

            out.append(line)

    @staticmethod
    def _append_pumps(parameters, out):

        out.append(InpFile.build_section_keyword(Pump.section_name))
        out.append(Pump.section_header)
        out.append(InpFile.build_dashline(Pump.section_header))

        p_fts = parameters.pumps_vlay.getFeatures()
        for p_ft in p_fts:
            eid = p_ft.attribute(Pump.field_name_eid)

            # Find start/end nodes
            adj_nodes = NetworkUtils.find_start_end_nodes(parameters, p_ft.geometry(), False, True, True)
            start_node_id = adj_nodes[0].attribute(Junction.field_name_eid)
            end_node_id = adj_nodes[1].attribute(Junction.field_name_eid)

            # Parameters
            pump_param = p_ft.attribute(Pump.field_name_param)
            value = p_ft.attribute(Pump.field_name_value)

            # Line
            line = InpFile.pad(eid)
            line += InpFile.pad(start_node_id)
            line += InpFile.pad(end_node_id)

            if pump_param == Pump.parameters_power:
                line += InpFile.pad(pump_param + ' ' + '{0:2f}'.format(value))
            elif pump_param == Pump.parameters_head:
                line += InpFile.pad(pump_param + ' ' + value)
            else:
                # TODO: add support for speed and pattern?
                line += '0'

            out.append(line)

    @staticmethod
    def _append_valves(parameters, out):

        out.append(InpFile.build_section_keyword(Valve.section_name))
        out.append(Valve.section_header)
        out.append(InpFile.build_dashline(Valve.section_header))

        v_fts = parameters.valves_vlay.getFeatures()
        for v_ft in v_fts:
            eid = v_ft.attribute(Valve.field_name_eid)

            # Find start/end nodes
            adj_nodes = NetworkUtils.find_start_end_nodes(parameters, v_ft.geometry(), False, True, True)
            start_node_id = adj_nodes[0].attribute(Junction.field_name_eid)
            end_node_id = adj_nodes[1].attribute(Junction.field_name_eid)

            diameter = v_ft.attribute(Valve.field_name_diameter)
            valve_type = v_ft.attribute(Valve.field_name_type)
            setting = v_ft.attribute(Valve.field_name_setting)
            minor_loss = v_ft.attribute(Valve.field_name_minor_loss)

            # Line
            line = InpFile.pad(eid)
            line += InpFile.pad(start_node_id)
            line += InpFile.pad(end_node_id)
            line += InpFile.pad(diameter)
            line += InpFile.pad(valve_type)
            line += InpFile.pad(setting)
            line += InpFile.pad(minor_loss)

            out.append(line)

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
    def pad(text, blanks_nr=10):
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