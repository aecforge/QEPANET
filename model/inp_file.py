import codecs

from network import Title, Junction, Reservoir, Tank, Pipe, Pump, Valve, Coordinate, Vertex
from system_ops import Controls, Curve, Demand, Energy, Pattern, Rule, Status
import math
from ..model.options_report import Times, Report
from options_report import Options, Quality
from ..model.network_handling import NetworkUtils
from ..tools.parameters import Parameters


class InpFile:
    
    large_pad = 19
    
    def __init__(self):
        pass

    @staticmethod
    def read_patterns(params):

        start_line = None
        end_line = None
        with codecs.open(params.patterns_file, 'r', encoding='UTF-8') as inp_f:

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
            params.patterns = []
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

        params.patterns = patterns_d.values()

    @staticmethod
    def write_patterns(params, inp_file_path):

        # Rewrite whole file
        with codecs.open(inp_file_path, 'w', encoding='UTF-8') as p_file:

            out = []
            InpFile._append_patterns(params, out)

            for line in out:
                p_file.write(line + '\n')

            # InpFile.write_lines(p_file, InpFile.build_section_keyword(Pattern.section_name))
            # InpFile.write_lines(p_file, InpFile.build_comment(Pattern.section_header))
            #
            # for pattern in params.patterns:
            #     if pattern.desc is not None:
            #         InpFile.write_lines(p_file, InpFile.build_comment(pattern.desc))
            #     InpFile.write_lines(p_file, InpFile.from_values_to_lines(pattern.values, line_header=pattern.id, vals_per_line=6))

    @staticmethod
    def write_lines(inp_file, lines):

        if type(lines) is str:
            inp_file.write(lines + '\n')
        else:
            for line in lines:
                inp_file.write(line + '\n')

    @staticmethod
    def read_curves(params):

        start_line = None
        end_line = None
        with codecs.open(params.curves_file, 'r', encoding='UTF-8') as inp_f:

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
                    curves_d[words[0]] = Curve(words[0], lines[l-1][1:])
                    x = words[1]
                    y = words[2]
                    curves_d[words[0]].append_xy(x, y)
                    continue
                else:
                    x = words[1]
                    y = words[2]
                    curves_d[words[0]].append_xy(x, y)

        params.curves = curves_d.values()

    @staticmethod
    def write_curves(params, inp_file_curve):

        # Rewrite whole file
        with codecs.open(inp_file_curve, 'w', encoding='UTF-8') as c_file:
            out = []
            InpFile._append_curves(params, out)

            for line in out:
                c_file.write(line + '\n')

    @staticmethod
    def write_inp_file(params, inp_file_path, title):

        out = []

        with codecs.open(inp_file_path, 'w', encoding='UTF-8') as inp_f:

            # Network --------------------
            # Title
            if title is not None:
                out.extend(InpFile.build_section_keyword(Title.section_name))
                out.extend(InpFile.split_line(title))

            # Junctions
            InpFile._append_junctions(params, out)

            # Reservoirs
            InpFile._append_reservoirs(params, out)

            # Tanks
            InpFile._append_tanks(params, out)

            # Pipes
            InpFile._append_pipes(params, out)

            # Pumps
            InpFile._append_pumps(params, out)

            # Valves
            InpFile._append_valves(params, out)

            # Emitters
            # TODO

            # SYSTEM OPERATIONS
            # Curves
            InpFile._append_curves(params, out)

            # Patterns
            InpFile._append_patterns(params, out)

            # Energy
            InpFile._append_energy(params, out)

            # Status
            InpFile._append_status(params, out)

            # Controls
            InpFile._append_controls(params, out)

            # Rules
            InpFile._append_rules(params, out)

            # Demands
            InpFile._append_demands(params, out)

            # WATER QUALITY
            # Quality
            # TODO

            # Reactions
            # TODO

            # Sources
            # TODO

            # Mixing
            # TODO

            # OPTIONS AND REPORTING
            # Options / reporting
            InpFile._append_options(params, out)

            # Times
            InpFile._append_times(params, out)

            # NETWORK MAP/TAG
            # Coordinates
            InpFile._append_coordinates(params, out)

            # Vertices
            InpFile._append_vertices(params, out)

            # Labels
            # NO

            # Backdrop
            # NO

            # Tags
            # NO

            # Write
            for line in out:
                inp_f.write(line + '\n')

    @staticmethod
    def _append_controls(params, out):
        out.extend(InpFile.build_section_keyword(Controls.section_name))

    @staticmethod
    def _append_coordinates(params, out):
        out.extend(InpFile.build_section_keyword(Coordinate.section_name))
        out.append(InpFile.build_section_header(Coordinate.section_header))
        out.append(InpFile.build_dashline(Coordinate.section_header))

        for j_ft in params.junctions_vlay.getFeatures():
            eid = j_ft.attribute(Junction.field_name_eid)
            pt = j_ft.geometry().asPoint()

            line = InpFile.pad(eid, InpFile.large_pad)
            line += InpFile.pad('{0:.2f}'.format(pt.x()), InpFile.large_pad)
            line += InpFile.pad('{0:.2f}'.format(pt.y()), InpFile.large_pad)

            out.append(line)

        for r_ft in params.reservoirs_vlay.getFeatures():
            eid = r_ft.attribute(Reservoir.field_name_eid)
            pt = r_ft.geometry().asPoint()

            line = InpFile.pad(eid, InpFile.large_pad)
            line += InpFile.pad('{0:.2f}'.format(pt.x()), InpFile.large_pad)
            line += InpFile.pad('{0:.2f}'.format(pt.y()), InpFile.large_pad)

            out.append(line)

        for t_ft in params.tanks_vlay.getFeatures():
            eid = t_ft.attribute(Tank.field_name_eid)
            pt = t_ft.geometry().asPoint()

            line = InpFile.pad(eid, InpFile.large_pad)
            line += InpFile.pad('{0:.2f}'.format(pt.x()), InpFile.large_pad)
            line += InpFile.pad('{0:.2f}'.format(pt.y()), InpFile.large_pad)

            out.append(line)

    @staticmethod
    def _append_curves(params, out):
        out.extend(InpFile.build_section_keyword(Curve.section_name))

        for curve in params.curves:
            if curve.desc is not None:
                out.extend(InpFile.build_comment(curve.desc))

            for v in range(len(curve.xs)):
                out.append(
                    InpFile.pad(str(curve.id), InpFile.large_pad) +
                    InpFile.pad(str(curve.xs[v])) +
                    InpFile.pad(str(curve.ys[v])))

    @staticmethod
    def _append_demands(params, out):
        out.extend(InpFile.build_section_keyword(Demand.section_name))

    @staticmethod
    def _append_energy(params, out):
        out.extend(InpFile.build_section_keyword(Energy.section_name))

        out.append(InpFile.pad('GLOBAL EFFICIENCY', InpFile.large_pad) + str(params.energy.pump_efficiency))
        out.append(InpFile.pad('GLOBAL PRICE', InpFile.large_pad) + str(params.energy.energy_price))
        out.append(InpFile.pad('DEMAND CHARGE', InpFile.large_pad) + str(params.energy.demand_charge))

    @staticmethod
    def _append_junctions(params, out):

        out.extend(InpFile.build_section_keyword(Junction.section_name))
        out.append(InpFile.build_section_header(Junction.section_header))
        # out.append(InpFile.build_dashline(Junction.section_header))

        j_fts = params.junctions_vlay.getFeatures()
        for j_ft in j_fts:
            eid = j_ft.attribute(Junction.field_name_eid)
            demand = j_ft.attribute(Junction.field_name_demand)
            elev = j_ft.attribute(Junction.field_name_elevation)
            elev_corr = j_ft.attribute(Junction.field_name_elev_corr)
            pattern = j_ft.attribute(Junction.field_name_pattern)

            if elev_corr is None:
                elev_corr = 0

            elev += elev_corr

            # Line
            line = InpFile.pad(eid, InpFile.large_pad)
            line += InpFile.pad('{0:.2f}'.format(elev))
            if demand is not None:
                line += InpFile.pad('{0:.5f}'.format(demand))
            else:
                line += InpFile.pad('')

            if pattern is not None:
                line += InpFile.pad(str(pattern))
            else:
                line += InpFile.pad('')

            out.append(line)

    @staticmethod
    def _append_options(params, out):

        # Options
        out.extend(InpFile.build_section_keyword(Options.section_name))

        out.append(InpFile.pad('UNITS', InpFile.large_pad) + params.options.flow_units)
        out.append(InpFile.pad('HEADLOSS', InpFile.large_pad) + params.options.headloss)
        if params.options.hydraulics.use_hydraulics:
            out.append(InpFile.pad('HYDRAULICS', InpFile.large_pad) + params.options.hydraulics.action_names[params.options.hydraulics.action])

        # Quality
        quality_line = InpFile.pad('QUALITY', InpFile.large_pad) + InpFile.pad(params.options.quality.quality_text[params.options.quality.parameter])
        if params.options.quality.parameter == Quality.quality_chemical:
            quality_line += InpFile.pad(params.options.quality.mass_units)
        elif params.options.quality.parameter == Quality.quality_trace:
            quality_line += InpFile.pad(params.options.quality.trace_junction_id)

        out.append(InpFile.pad('VISCOSITY', InpFile.large_pad) + str(params.options.viscosity))
        out.append(InpFile.pad('DIFFUSIVITY', InpFile.large_pad) + str(params.options.diffusivity))
        out.append(InpFile.pad('SPECIFIC GRAVITY', InpFile.large_pad) + str(params.options.spec_gravity))
        out.append(InpFile.pad('TRIALS', InpFile.large_pad) + str(params.options.trials))
        out.append(InpFile.pad('ACCURACY', InpFile.large_pad) + str(params.options.accuracy))
        out.append(InpFile.pad('UNBALANCED', InpFile.large_pad) +
                   params.options.unbalanced.unb_text[params.options.unbalanced.unbalanced] +
                   ' ' +
                   str(params.options.unbalanced.trials))
        out.append(InpFile.pad('PATTERN', InpFile.large_pad) + str(params.options.pattern))
        out.append(InpFile.pad('DEMAND MULTIPLIER', InpFile.large_pad) + str(params.options.demand_mult))
        out.append(InpFile.pad('EMITTER EXPONENT', InpFile.large_pad) + str(params.options.emitter_exp))
        out.append(InpFile.pad('TOLERANCE', InpFile.large_pad) + str(params.options.tolerance))

        # Report
        out.extend(InpFile.build_section_keyword(Report.section_name))

        out.append(InpFile.pad('PAGESIZE', InpFile.large_pad) + str(params.report.page_size))
        if params.report.file is not None:
            out.append(InpFile.pad('FILE', InpFile.large_pad) + str(params.report.file))
        out.append(InpFile.pad('STATUS', InpFile.large_pad) + params.report.statuses_names[params.report.status])
        out.append(InpFile.pad('SUMMARY', InpFile.large_pad) + params.report.summary_names[params.report.summary])
        out.append(InpFile.pad('ENERGY', InpFile.large_pad) + params.report.energy_names[params.report.energy])

        # TODO: nodes and links need support for multi-line
        nodes_line = InpFile.pad('NODES', InpFile.large_pad)
        if params.report.nodes == params.report.nodes_none or params.report.nodes == params.report.nodes_all:
            nodes_line += params.report.nodes_names[params.report.nodes]
        else:
            nodes_ids = ''
            for node_id in params.report.nodes_ids:
                nodes_ids += node_id + ' '
            nodes_line += nodes_ids

        out.append(nodes_line)

        links_line = InpFile.pad('LINKS', InpFile.large_pad)
        if params.report.links == params.report.links_none or params.report.links == params.report.links_all:
            links_line += params.report.links_names[params.report.links]
        else:
            links_ids = ''
            for link_id in params.report.links_ids:
                links_ids += link_id + ' '
                links_line += links_ids

        out.append(links_line)

    @staticmethod
    def _append_patterns(params, out):
        out.extend(InpFile.build_section_keyword(Pattern.section_name))

        for pattern in params.patterns:
            if pattern.desc is not None:
                out.extend(InpFile.build_comment(pattern.desc))

            lines = InpFile.from_values_to_lines(pattern.values, line_header=pattern.id, vals_per_line=6)
            for line in lines:
                out.append(line)

    @staticmethod
    def _append_pipes(params, out):

        out.extend(InpFile.build_section_keyword(Pipe.section_name))
        out.append(InpFile.build_section_header(Pipe.section_header))
        # out.append(InpFile.build_dashline(Pipe.section_header))

        p_fts = params.pipes_vlay.getFeatures()
        for p_ft in p_fts:
            eid = p_ft.attribute(Pipe.field_name_eid)

            # Find start/end nodes
            adj_nodes = NetworkUtils.find_start_end_nodes(params, p_ft.geometry())
            start_node_id = adj_nodes[0].attribute(Junction.field_name_eid)
            end_node_id = adj_nodes[1].attribute(Junction.field_name_eid)

            length = p_ft.attribute(Pipe.field_name_length)
            diameter = p_ft.attribute(Pipe.field_name_diameter)
            roughness = p_ft.attribute(Pipe.field_name_roughness)
            minor_loss = p_ft.attribute(Pipe.field_name_minor_loss)
            status = p_ft.attribute(Pipe.field_name_status)

            # Line
            line = InpFile.pad(eid, InpFile.large_pad)
            line += InpFile.pad(start_node_id, InpFile.large_pad)
            line += InpFile.pad(end_node_id, InpFile.large_pad)
            line += InpFile.pad('{0:.2f}'.format(length), InpFile.large_pad)
            line += InpFile.pad('{0:.2f}'.format(diameter))
            line += InpFile.pad('{0:.2f}'.format(roughness))
            line += InpFile.pad('{0:.2f}'.format(minor_loss))
            line += InpFile.pad(status)

            out.append(line)

    @staticmethod
    def _append_pumps(params, out):

        out.extend(InpFile.build_section_keyword(Pump.section_name))
        out.append(InpFile.build_section_header(Pump.section_header))
        # out.append(InpFile.build_dashline(Pump.section_header))

        p_fts = params.pumps_vlay.getFeatures()
        for p_ft in p_fts:
            eid = p_ft.attribute(Pump.field_name_eid)

            # Find start/end nodes
            adj_nodes = NetworkUtils.find_start_end_nodes(params, p_ft.geometry(), False, True, True)
            start_node_id = adj_nodes[0].attribute(Junction.field_name_eid)
            end_node_id = adj_nodes[1].attribute(Junction.field_name_eid)

            # Parameters
            pump_param = p_ft.attribute(Pump.field_name_param)
            value = p_ft.attribute(Pump.field_name_value)

            # Line
            line = InpFile.pad(eid, InpFile.large_pad)
            line += InpFile.pad(start_node_id, InpFile.large_pad)
            line += InpFile.pad(end_node_id, InpFile.large_pad)

            if pump_param == Pump.parameters_power:
                line += InpFile.pad(pump_param + ' ' + '{0:2f}'.format(value), InpFile.large_pad)
            elif pump_param == Pump.parameters_head:
                line += InpFile.pad(pump_param + ' ' + value, InpFile.large_pad)
            else:
                # TODO: add support for speed and pattern?
                line += '0'

            out.append(line)

    @staticmethod
    def _append_rules(params, out):
        out.extend(InpFile.build_section_keyword(Rule.section_name))

    @staticmethod
    def _append_status(params, out):
        out.extend(InpFile.build_section_keyword(Status.section_name))
        out.append(InpFile.build_section_header(Status.section_header))

    @staticmethod
    def _append_reservoirs(params, out):

        out.extend(InpFile.build_section_keyword(Reservoir.section_name))
        out.append(InpFile.build_section_header(Reservoir.section_header))
        # out.append(InpFile.build_dashline(Reservoir.section_header))

        r_fts = params.reservoirs_vlay.getFeatures()
        for r_ft in r_fts:
            eid = r_ft.attribute(Reservoir.field_name_eid)
            elev = r_ft.attribute(Reservoir.field_name_elevation)
            elev_corr = r_ft.attribute(Reservoir.field_name_elev_corr)
            head = r_ft.attribute(Reservoir.field_name_head)
            # pattern = r_ft.attribute(Reservoir.field_name_pattern) # TODO: add support for pattern

            if elev is None:
                elev = 0
            if elev_corr is None:
                elev_corr = 0

            head += elev + elev_corr

            # Line
            line = InpFile.pad(eid, InpFile.large_pad)
            line += InpFile.pad('{0:.2f}'.format(head))
            # line += InpFile.pad(pattern)

            out.append(line)

    @staticmethod
    def _append_tanks(params, out):

        out.extend(InpFile.build_section_keyword(Tank.section_name))
        out.append(InpFile.build_section_header(Tank.section_header))
        # out.append(InpFile.build_dashline(Tank.section_header))

        t_fts = params.tanks_vlay.getFeatures()
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
            line = InpFile.pad(eid, InpFile.large_pad)
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
    def _append_times(params, out):

        out.extend(InpFile.build_section_keyword(Times.section_name))
        out.append(InpFile.pad('DURATION', InpFile.large_pad) + str(params.times.duration))

        out.append(InpFile.pad('HYDRAULIC TIMESTAMP', InpFile.large_pad) + params.times.hydraulic_timestamp.get_as_text())
        out.append(InpFile.pad('QUALITY TIMESTAMP', InpFile.large_pad) + params.times.quality_timestamp.get_as_text())
        out.append(InpFile.pad('RULE TIMESTAMP', InpFile.large_pad) + params.times.rule_timestamp.get_as_text())
        out.append(InpFile.pad('PATTERN TIMESTAMP', InpFile.large_pad) + params.times.pattern_timestamp.get_as_text())
        out.append(InpFile.pad('PATTERN START', InpFile.large_pad) + params.times.pattern_start.get_as_text())
        out.append(InpFile.pad('REPORT TIMESTAMP', InpFile.large_pad) + params.times.report_timestamp.get_as_text())
        out.append(InpFile.pad('REPORT START', InpFile.large_pad) + params.times.report_start.get_as_text())
        out.append(InpFile.pad('START CLOCKTIME', InpFile.large_pad) + params.times.clocktime_start.get_as_text())
        out.append(InpFile.pad('STATISTIC', InpFile.large_pad) + str(params.times.statistic))

    @staticmethod
    def _append_valves(params, out):

        out.extend(InpFile.build_section_keyword(Valve.section_name))
        out.append(InpFile.build_section_header(Valve.section_header))
        # out.append(InpFile.build_dashline(Valve.section_header))

        v_fts = params.valves_vlay.getFeatures()
        for v_ft in v_fts:
            eid = v_ft.attribute(Valve.field_name_eid)

            # Find start/end nodes
            adj_nodes = NetworkUtils.find_start_end_nodes(params, v_ft.geometry(), False, True, True)
            start_node_id = adj_nodes[0].attribute(Junction.field_name_eid)
            end_node_id = adj_nodes[1].attribute(Junction.field_name_eid)

            diameter = v_ft.attribute(Valve.field_name_diameter)
            valve_type = v_ft.attribute(Valve.field_name_type)
            setting = v_ft.attribute(Valve.field_name_setting)
            minor_loss = v_ft.attribute(Valve.field_name_minor_loss)

            # Line
            line = InpFile.pad(eid, InpFile.large_pad)
            line += InpFile.pad(start_node_id, InpFile.large_pad)
            line += InpFile.pad(end_node_id, InpFile.large_pad)
            line += InpFile.pad(str(diameter))
            line += InpFile.pad(valve_type)
            line += InpFile.pad(setting)
            line += InpFile.pad(minor_loss)

            out.append(line)

    @staticmethod
    def _append_vertices(params, out):
        out.extend(InpFile.build_section_keyword(Vertex.section_name))
        out.append(InpFile.build_section_header(Vertex.section_header))
        # out.append(InpFile.build_dashline(Vertex.section_header))

        for p_ft in params.pipes_vlay.getFeatures():
            eid = p_ft.attribute(Pipe.field_name_eid)
            pts = p_ft.geometry().asPolyline()
            if len(pts) > 2:
                for pt in pts[1:-1]:
                    line = InpFile.pad(eid, InpFile.large_pad)
                    line += InpFile.pad('{0:.2f}'.format(pt.x()), InpFile.large_pad)
                    line += InpFile.pad('{0:.2f}'.format(pt.y()), InpFile.large_pad)

                    out.append(line)

    @staticmethod
    def split_line(line, n=255):
        lines = [line[i:i + n] for i in range(0, len(line), n)]
        return lines

    @staticmethod
    def from_values_to_lines(values, decimal_places=2, n=255, element_size=10, line_header=None, vals_per_line=None):

        if line_header is not None:
            header = str(InpFile.pad(line_header, InpFile.large_pad))
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
        return ['',
                '[' + section_name + ']']

    @staticmethod
    def build_section_header(section_header):
        return ';' + section_header

    @staticmethod
    def build_comment(comment):
        comments = InpFile.split_line(comment)
        for c in range(len(comments)):
            comments[c] = ';' + comments[c]
        return comments

    @staticmethod
    def build_dashline(text):
        dashline = ';'
        for d in range(len(text)):
            dashline += '-'
        return dashline