from collections import OrderedDict
import os, struct


class BinaryOutputReader:

    def __init__(self, out_file):

        with open(out_file, 'rb') as f:

            self.file_size = os.path.getsize(out_file)

            # Prolog --------------------------------------------------------------------------------------------------
            self.magic_nr = struct.unpack('I', f.read(4))[0]
            self.version = struct.unpack('I', f.read(4))[0]
            self.nodes_nr = struct.unpack('I', f.read(4))[0]
            self.tanks_reservs_nr = struct.unpack('I', f.read(4))[0]
            self.links_nr = struct.unpack('I', f.read(4))[0]
            self.pumps_nr = struct.unpack('I', f.read(4))[0]
            self.valves_nr = struct.unpack('I', f.read(4))[0]

            # Water quality:
            # 0 = None
            # 1 = Chemical
            # 2 = Age
            # 3 = Source trace
            self.w_quality_option = struct.unpack('I', f.read(4))[0]
            self.source_trace_idx = struct.unpack('I', f.read(4))[0]

            # Flow units
            # 0 = cfs
            # 1 = gpm
            # 2 = mgd
            # 3 = Imperial mgd
            # 4 = acre - ft / day
            # 5 = liters / second
            # 6 = liters / minute
            # 7 = megaliters / day
            # 8 = cubic  meters / hour
            # 9 = cubic meters / day
            self.flow_units = struct.unpack('I', f.read(4))[0]

            # Pressure
            # 0 = psi
            # 1 = meters
            # 2 = kPa
            self.pressure_units = struct.unpack('I', f.read(4))[0]

            # Statistics
            # 0 = no statistical processing
            # 1 = results are time - averaged
            # 2 = only minimum values reported
            # 3 = only maximum values reported
            # 4 = only ranges reported
            self.statistics_flag = struct.unpack('I', f.read(4))

            self.report_start_time_secs = struct.unpack('I', f.read(4))[0]
            self.report_time_step_secs = struct.unpack('I', f.read(4))[0]
            self.sim_duration_secs = struct.unpack('I', f.read(4))[0]
            self.title_1 = ''.join(struct.unpack('c' * 80, f.read(80)))
            self.title_2 = ''.join(struct.unpack('c' * 80, f.read(80)))
            self.title_3 = ''.join(struct.unpack('c' * 80, f.read(80)))

            self.inp_file_name = ''.join(struct.unpack('c' * 260, f.read(260)))
            self.rpt_file_name = ''.join(struct.unpack('c' * 260, f.read(260)))

            self.chem_name = ''.join(struct.unpack('c' * 16, f.read(16)))
            self.chem_conc_units = ''.join(struct.unpack('c' * 16, f.read(16)))
            self.node_id_label = ''.join(struct.unpack('c' * 16, f.read(16)))
            self.link_id_label = ''.join(struct.unpack('c' * 16, f.read(16)))

            nodes_ids = []
            for i in range(self.nodes_nr):
                nodes_ids.append(f.read(32).replace('\00', ''))

            links_ids = []
            for i in range(self.links_nr):
                links_ids.append(f.read(32).replace('\00', ''))

            link_start_node_idxs = []
            for i in range(self.links_nr):
                link_start_node_idxs.append(struct.unpack('I', f.read(4))[0])

            link_end_node_idxs = []
            for i in range(self.links_nr):
                link_end_node_idxs.append(struct.unpack('I', f.read(4))[0])

            link_codes = []
            for i in range(self.links_nr):
                link_codes.append(struct.unpack('I', f.read(4))[0])

            tanks_reservs_idxs = []
            for i in range(self.tanks_reservs_nr):
                tanks_reservs_idxs.append(struct.unpack('I', f.read(4))[0])

            # 0 == Reservoir
            tanks_reservs_cross_sects = []
            for i in range(self.tanks_reservs_nr):
                tanks_reservs_cross_sects.append(struct.unpack('f', f.read(4))[0])

            nodes_elevs = []
            for i in range(self.nodes_nr):
                nodes_elevs.append(struct.unpack('f', f.read(4))[0])

            link_lengths = []
            for i in range(self.links_nr):
                link_lengths.append(struct.unpack('f', f.read(4))[0])

            link_diams = []
            for i in range(self.links_nr):
                link_diams.append(struct.unpack('f', f.read(4))[0])

            # Energy use -----------------------------------------------------------------------------------------------
            self.pumps = []
            for i in range(self.pumps_nr):
                idx = struct.unpack('I', f.read(4))[0]
                util = struct.unpack('f', f.read(4))[0]
                effic = struct.unpack('f', f.read(4))[0]
                avg_kw_mg = struct.unpack('f', f.read(4))[0]
                avg_kw = struct.unpack('f', f.read(4))[0]
                peak_kw = struct.unpack('f', f.read(4))[0]
                avg_day_cost = struct.unpack('f', f.read(4))[0]
                self.pumps.append(Pump(idx, util, effic, avg_kw_mg, avg_kw, peak_kw, avg_day_cost, peak_cost))
            self.peak_cost = struct.unpack('f', f.read(4))[0]

            results_pt_pos = f.tell()

            # Epilog (28 bytes)
            f.seek(self.file_size - 28)
            self.avg_bulk_react_rate = struct.unpack('f', f.read(4))[0]
            self.avg_wall_react_rate = struct.unpack('f', f.read(4))[0]
            self.avg_tank_react_rate = struct.unpack('f', f.read(4))[0]
            self.avg_source_inflow_rate = struct.unpack('f', f.read(4))[0]
            self.reporting_periods = struct.unpack('I', f.read(4))[0]
            self.warning_flag = struct.unpack('I', f.read(4))[0]
            self.magic_nr_2 = struct.unpack('I', f.read(4))[0]

            # Dynamic results-------------------------------------------------------------------------------------------
            f.seek(results_pt_pos)
            self.period_results = OrderedDict()
            for rp in range(self.reporting_periods):

                report_time = self.report_time_step_secs * rp

                self.node_demands_d = OrderedDict()
                self.node_heads_d = OrderedDict()
                self.node_pressures_d = OrderedDict()
                self.node_qualities_d = OrderedDict()

                self.link_flows_d = OrderedDict()
                self.link_velocities_d = OrderedDict()
                self.link_headloss_d = OrderedDict()
                self.link_qualities_d = OrderedDict()
                self.link_status_codes_d = OrderedDict()
                self.link_settings_d = OrderedDict()
                self.link_reactions_d = OrderedDict()
                self.link_frictions_d = OrderedDict()

                # Nodes
                for i in range(self.nodes_nr):
                    self.node_demands_d[nodes_ids[i]] = struct.unpack('f', f.read(4))[0]

                for i in range(self.nodes_nr):
                    self.node_heads_d[nodes_ids[i]] = struct.unpack('f', f.read(4))[0]

                for i in range(self.nodes_nr):
                    self.node_pressures_d[nodes_ids[i]] = struct.unpack('f', f.read(4))[0]

                for i in range(self.nodes_nr):
                    self.node_qualities_d[nodes_ids[i]] = struct.unpack('f', f.read(4))[0]

                # Links
                for i in range(self.links_nr):
                    self.link_flows_d[links_ids[i]] = struct.unpack('f', f.read(4))[0]

                for i in range(self.links_nr):
                    self.link_velocities_d[links_ids[i]] = struct.unpack('f', f.read(4))[0]

                for i in range(self.links_nr):
                    self.link_headloss_d[links_ids[i]] = struct.unpack('f', f.read(4))[0]

                for i in range(self.links_nr):
                    self.link_qualities_d[links_ids[i]] = struct.unpack('f', f.read(4))[0]

                for i in range(self.links_nr):
                    self.link_status_codes_d[links_ids[i]] = struct.unpack('f', f.read(4))[0]

                for i in range(self.links_nr):
                    self.link_settings_d[links_ids[i]] = struct.unpack('f', f.read(4))[0]

                for i in range(self.links_nr):
                    self.link_reactions_d[links_ids[i]] = struct.unpack('f', f.read(4))[0]

                for i in range(self.links_nr):
                    self.link_frictions_d[links_ids[i]] = struct.unpack('f', f.read(4))[0]

                self.period_results[report_time] = PeriodResult(
                    self.node_demands_d, self.node_heads_d, self.node_pressures_d, self.node_qualities_d,
                    self.link_flows_d, self.link_velocities_d, self.link_headloss_d, self.link_qualities_d,
                    self.link_status_codes_d, self.link_settings_d, self.link_reactions_d, self.link_frictions_d)


class Pump:
    def __init__(self, idx, util, effic, avg_kw_mg, avg_kw, peak_kw, avg_day_cost, peak_cost):
        self.idx = idx
        self.util = util
        self.effic = effic
        self.idx = avg_kw_mg
        self.avg_kw = avg_kw
        self.peak_kw = peak_kw
        self.avg_day_cost = avg_day_cost
        self.peak_cost = peak_cost


class PeriodResult:

    def __init__(self, node_demands, node_heads, node_pressures, node_qualities, link_flows, link_velocities,
                 link_headloss, link_qualities, link_status_codes, link_settings, link_reactions, link_frictions):

        self.node_demands = node_demands
        self.node_heads = node_heads
        self.node_pressures = node_pressures
        self.node_qualities = node_qualities

        self.link_flows = link_flows
        self.link_velocities = link_velocities
        self.link_headloss = link_headloss
        self.link_qualities = link_qualities
        self.link_status_codes = link_status_codes
        self.link_settings = link_settings
        self.link_reactions = link_reactions
        self.link_frictions = link_frictions

#
# bor = BinaryOutputReader('D:/Progetti/2015/2015_13_TN_EPANET/04_Implementation/INP_Test/Test_cases/1/1.out')
# for key, value in bor.period_results.iteritems():
#     print key
#     for id, demand in value.node_demands.iteritems():
#         print id, demand
