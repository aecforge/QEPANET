# Modified from https://plugins.qgis.org/plugins/ImportEpanetInpFiles/
# (C)Marios Kyriakou 2016
# University of Cyprus, KIOS Research Center for Intelligent Systems and Networks

from network import *

import readEpanetFile as d
import os
from inp_writer import InpFile
from ..tools.data_stores import MemoryDS
from .options_report import Options, Unbalanced, Quality, Report, Hour, Times
import codecs


class InpReader:

    def __init__(self, inp_path):
        self.params = None
        self.inp_path = inp_path

        with codecs.open(self.inp_path, 'r', encoding='UTF-8') as inp_f:
            self.lines = inp_f.read().splitlines()

    def read(self, params):

        self.inp_path = self.inp_path
        self.params = params

        statinfo = os.stat(self.inp_path)
        file_size = statinfo.st_size
        if file_size == 0:
            return None

        d.LoadFile(self.inp_path)
        d.BinUpdateClass()
        links_count = d.getBinLinkCount()

        # Get all Sections
        mixing = d.getMixingSection()
        reactions = d.getReactionsSection()
        sources = d.getSourcesSection()
        rules = d.getRulesSection()
        quality = d.getQualitySection()
        curves = d.getCurvesSection()
        patterns = d.getPatternsSection()
        controls = d.getControlsSection()
        emitters = d.getEmittersSection()
        emitters_d = {}
        for emitter in emitters:
            emitters_d[emitter[0]] = emitter[1]

        status = d.getStatusSection()
        demands = d.getDemandsSection()
        energy = d.getEnergySection()
        opt_reactions = d.getReactionsOptionsSection()
        times = d.getTimesSection()
        report = d.getReportSection()
        options = d.getOptionsSection()

        # Check for QEPANET section in inp file. If it's there, update layer attributes
        qepanet_junctions_od = self.read_qepanet_junctions()
        qepanet_tanks_od = self.read_qepanet_tanks()
        (qepanet_reservoirs_deltaz_od, qepanet_reservoirs_press_head_od) = self.read_qepanet_reservoirs()
        qepanet_pipes_od = self.read_qepanet_pipes()
        qepanet_vertices_od = self.read_qepanet_vertices()

        # Create layers and update
        if mixing:
            self.update_mixing(mixing)
        if reactions:
            self.update_reactions(reactions)
        if sources:
            self.update_sources(sources)
        if rules:
            self.update_rules(rules)
        if quality:
            self.update_quality(quality)
        if curves:
            self.update_curves()
        if patterns:
            self.update_patterns()
        if controls:
            self.update_controls(controls)
        if demands:
            self.update_demands(demands)
        if energy:
            self.update_energy(energy)
        if opt_reactions:
            self.update_opt_reactions(opt_reactions)
        if times:
            self.update_times(times)
        if report:
            self.update_report(report)
        if options:
            self.update_options(options)

        # Get all Section lengths
        all_sections = [len(energy), len(opt_reactions), len(demands), len(status), len(emitters), len(controls),
                       len(patterns),
                       len(curves[0]), len(quality), len(rules), len(sources), len(reactions), len(mixing), len(times),
                       len(report),
                       len(options), d.getBinNodeCount(), d.getBinLinkCount()]
        ss = max(all_sections)

        xy = d.getBinNodeCoordinates()

        x = xy[0]
        y = xy[1]
        vertx = xy[2]
        verty = xy[3]
        vertxyFinal = []
        for i in range(len(vertx)):
            vertxy = []
            for u in range(len(vertx[i])):
                vertxy.append([float(vertx[i][u]), float(verty[i][u])])
            if vertxy != []:
                vertxyFinal.append(vertxy)

        # Get data of Junctions
        ndEle = d.getBinNodeJunctionElevations()
        ndBaseD = d.getBinNodeBaseDemands()
        ndID = d.getBinNodeNameID()
        ndPatID = d.getBinNodeDemandPatternID()

        junctions_lay = None
        if d.getBinNodeJunctionCount() > 0:

            junctions_lay = MemoryDS.create_junctions_lay(crs=params.crs)
            junctions_lay_dp = junctions_lay.dataProvider()

        # Get data of Pipes
        # Write shapefile pipe
        pipes_lay = None
        pumps_lay = None
        valves_lay = None

        if links_count > 0:

            # Pipes
            pipes_lay = MemoryDS.create_pipes_lay(crs=params.crs)
            pipes_lay_dp = pipes_lay.dataProvider()

            # Pumps
            pumps_lay = MemoryDS.create_pumps_lay(crs=params.crs)
            pumps_lay_dp = pumps_lay.dataProvider()

            # Valves
            valves_lay = MemoryDS.create_valves_lay(crs=params.crs)
            valves_lay_dp = valves_lay.dataProvider()

            pump_index = d.getBinLinkPumpIndex()
            valve_index = d.getBinLinkValveIndex()
            ndlConn = d.getBinNodesConnectingLinksID()
            x1 = []
            x2 = []
            y1 = []
            y2 = []
            stat = d.getBinLinkInitialStatus()

            kk = 0
            ch = 0
            linkID = d.getBinLinkNameID()
            linkLengths = d.getBinLinkLength()
            linkDiameters = d.getBinLinkDiameter()
            linkRough = d.getBinLinkRoughnessCoeff()
            linkMinorloss = d.getBinLinkMinorLossCoeff()

        # Write Tank Shapefile and get tank data
        tanks_lay = None
        if d.getBinNodeTankCount() > 0:
            tanks_lay = MemoryDS.create_tanks_lay(crs=params.crs)
            tanks_lay_dp = tanks_lay.dataProvider()

            ndTankelevation = d.getBinNodeTankElevations()
            initiallev = d.getBinNodeTankInitialLevel()
            minimumlev = d.getBinNodeTankMinimumWaterLevel()
            maximumlev = d.getBinNodeTankMaximumWaterLevel()
            diameter = d.getBinNodeTankDiameter()
            minimumvol = d.getBinNodeTankMinimumWaterVolume()
            volumecurv = d.getBinNodeTankVolumeCurveID()
            ndTankID = d.getBinNodeTankNameID()

        reservoirs_lay = None
        if d.getBinNodeReservoirCount() > 0:
            reservoirs_lay = MemoryDS.create_reservoirs_lay(crs=params.crs)
            reservoirs_lay_dp = reservoirs_lay.dataProvider()

            reservoirs_elev = d.getBinNodeReservoirElevations()
            # posReservoirs.startEditing()

        vvLink = 68
        bbLink = 1

        vPos = 0
        pPos = 0
        pPosPower = 0
        pPosHead = 0
        pPosSpeed = 0
        pPosSpeedPattern = 0

        for i in range(ss):
            if i == ss / vvLink and vvLink > -1:
                vvLink = vvLink - 1
                bbLink = bbLink + 1

            if i < d.getBinNodeJunctionCount():
                featJ = QgsFeature()
                point = QgsPoint(float(x[i]), float(y[i]))

                delta_z = 0
                if qepanet_junctions_od:
                    delta_z = qepanet_junctions_od[ndID[i]]

                featJ.setGeometry(QgsGeometry.fromPoint(point))

                # Emitter
                emitter_coeff = NULL
                if ndID[i] in emitters_d:
                    emitter_coeff = emitters_d[ndID[i]]

                featJ.setAttributes([ndID[i], ndEle[i] - delta_z, delta_z, ndPatID[i], ndBaseD[i], emitter_coeff])
                junctions_lay_dp.addFeatures([featJ])

            if i < links_count:
                if len(stat) == i:
                    ch = 1
                if ch == 1:
                    stat.append('OPEN')

                x1.append(x[ndID.index(d.getBinLinkFromNode()[i])])
                y1.append(y[ndID.index(d.getBinLinkFromNode()[i])])
                x2.append(x[ndID.index(d.getBinLinkToNode()[i])])
                y2.append(y[ndID.index(d.getBinLinkToNode()[i])])

                if i in pump_index:

                    # Pump
                    point1 = QgsPoint(float(x1[i]), float(y1[i]))
                    point2 = QgsPoint(float(x2[i]), float(y2[i]))

                    chPowerPump = d.getBinLinkPumpPower()
                    cheadpump = d.getBinLinkPumpCurveNameID()
                    pumpID = d.getBinLinkPumpNameID()
                    patternsIDs = d.getBinLinkPumpPatterns()
                    ppatt = d.getBinLinkPumpPatternsPumpID()
                    linkID = d.getBinLinkNameID()

                    Head = []
                    Flow = []
                    curve = []
                    power = []
                    pattern = []
                    pumpNameIDPower = d.getBinLinkPumpNameIDPower()

                    param = None
                    head = None
                    power = None
                    speed = 0

                    if pumpID[pPos] in pumpNameIDPower:
                        param = 'POWER'
                        power = chPowerPump[pPosPower]
                        pPosPower += 1
                    else:
                        param = 'HEAD'
                        head = cheadpump[pPosHead]
                        pPosHead += 1

                    if len(pumpNameIDPower) > 0:
                        for uu in range(0, len(pumpNameIDPower)):
                            if pumpNameIDPower[uu] == pumpID[pPos]:
                                power = chPowerPump[uu]
                    if len(patternsIDs) > 0:
                        for uu in range(0, len(ppatt)):
                            if ppatt[uu] == pumpID[pPos]:
                                pattern = patternsIDs[uu]

                    if d.getBinCurveCount() > 0 and len(pumpNameIDPower) == 0:
                        curveXY = d.getBinCurvesXY()
                        curvesID = d.getBinCurvesNameID()
                        for uu in range(0, len(curveXY)):
                            if curvesID[uu] == cheadpump[pPos]:
                                Head.append(str(curveXY[uu][0]))
                                Flow.append(str(curveXY[uu][1]))
                        curve = d.getBinLinkPumpCurveNameID()[pPos]

                    if pumpID[pPos] in d.getBinLinkPumpSpeedID():
                        speed = d.getBinLinkPumpSpeed()[pPosSpeed]
                        pPosSpeed += 1

                    pump_pattern = None
                    if pumpID[pPos] in ppatt:
                        pump_pattern = d.getBinLinkPumpPatterns()[pPosSpeedPattern]
                        pPosSpeedPattern += 1

                    pump_status = Pump.status_open
                    for statuss in status:
                        if statuss[0] == linkID[i]:
                            pump_status = statuss[1]
                            break

                    featPump = QgsFeature()
                    featPump.setGeometry(QgsGeometry.fromPolyline([point1, point2]))

                    featPump.setAttributes([linkID[i], param, head, power, speed, pump_pattern, pump_status])
                    pumps_lay_dp.addFeatures([featPump])

                    pPos += 1

                elif i in valve_index:
                    # Valve
                    point1 = QgsPoint(float(x1[i]), float(y1[i]))
                    point2 = QgsPoint(float(x2[i]), float(y2[i]))

                    length = 0
                    diameter = 0
                    roughness = 0
                    minorloss = 0
                    featValve = QgsFeature()
                    featValve.setGeometry((QgsGeometry.fromPolyline([point1, point2])))

                    linkID = d.getBinLinkValveNameID()
                    linkType = d.getBinLinkValveType()
                    linkDiameter = d.getBinLinkValveDiameters()
                    linkInitSett = d.getBinLinkValveSetting()
                    linkMinorloss = d.getBinLinkValveMinorLoss()

                    featValve.setAttributes(
                         [linkID[vPos], linkDiameter[vPos], linkType[vPos], linkInitSett[vPos], linkMinorloss[vPos]])
                    valves_lay_dp.addFeatures([featValve])

                    vPos += 1

                else:
                    # Pipe

                    # Last point
                    start_node_id = ndlConn[0][i]
                    end_node_id = ndlConn[1][i]

                    # Z
                    start_node_elev = 0
                    end_node_elev = 0
                    for j in range(d.getBinNodeJunctionCount()):

                        delta_z = 0
                        if qepanet_junctions_od and ndID[j] in qepanet_junctions_od:
                            delta_z = qepanet_junctions_od[ndID[j]]
                        if qepanet_reservoirs_deltaz_od and ndID[j] in qepanet_reservoirs_deltaz_od:
                            delta_z = qepanet_reservoirs_deltaz_od[ndID[j]]
                        if qepanet_tanks_od and ndID[j] in qepanet_tanks_od:
                            delta_z = qepanet_tanks_od[ndID[j]]

                        if ndID[j] == start_node_id:
                            start_node_elev = ndEle[j] + delta_z

                        if ndID[j] == end_node_id:
                            end_node_elev = ndEle[j] + delta_z

                    point1 = QgsPointV2(QgsWKBTypes.PointZ, float(x1[i]), float(y1[i]), start_node_elev)
                    point2 = QgsPointV2(QgsWKBTypes.PointZ, float(x2[i]), float(y2[i]), end_node_elev)

                    if vertx[i]:
                        parts = []
                        parts.append(point1)
                        for mm in range(len(vertxyFinal[kk])):
                            a = vertxyFinal[kk][mm]

                            z = 0
                            if linkID[i] in qepanet_vertices_od:
                                z = qepanet_vertices_od[linkID[i]]

                            parts.append(QgsPointV2(QgsWKBTypes.PointZ, a[0], a[1], z))

                        parts.append(point2)
                        featPipe = QgsFeature()
                        linestring = QgsLineStringV2()
                        linestring.setPoints(parts)
                        geom_3d = QgsGeometry(linestring)
                        featPipe.setGeometry(geom_3d)

                        kk += 1
                    else:
                        featPipe = QgsFeature()
                        # point1 = QgsPoint(float(x1[i]), float(y1[i]))
                        # point2 = QgsPoint(float(x2[i]), float(y2[i]))

                        linestring = QgsLineStringV2()
                        linestring.setPoints([point1, point2])
                        geom_3d = QgsGeometry(linestring)
                        featPipe.setGeometry(geom_3d)

                        # featPipe.setGeometry(QgsGeometry.fromPolyline([point1, point2]))

                    material = None
                    if linkID[i] in qepanet_pipes_od:
                        material = qepanet_pipes_od[linkID[i]]

                    featPipe.setAttributes(
                        [linkID[i], linkLengths[i], linkDiameters[i], stat[i],
                         linkRough[i], linkMinorloss[i], material])
                    pipes_lay_dp.addFeatures([featPipe])

            if i < d.getBinNodeTankCount():
                p = d.getBinNodeTankIndex()[i] - 1
                featTank = QgsFeature()
                point = QgsPoint(float(x[p]), float(y[p]))
                featTank.setGeometry(QgsGeometry.fromPoint(point))

                delta_z = 0
                if ndTankID[i] in qepanet_tanks_od:
                    delta_z = qepanet_tanks_od[ndTankID[i]]

                featTank.setAttributes(
                    [ndTankID[i], ndTankelevation[i] - delta_z, delta_z, initiallev[i], minimumlev[i], maximumlev[i], diameter[i],
                     minimumvol[i], volumecurv[i]])
                tanks_lay_dp.addFeatures([featTank])

            if i < d.getBinNodeReservoirCount():
                p = d.getBinNodeReservoirIndex()[i] - 1

                feature = QgsFeature()
                point = QgsPoint(float(x[p]), float(y[p]))
                feature.setGeometry(QgsGeometry.fromPoint(point))

                delta_z = 0
                if ndID[p] in qepanet_reservoirs_deltaz_od:
                    delta_z = qepanet_reservoirs_deltaz_od[ndID[p]]

                pressure_head = 0
                if ndID[p] in qepanet_reservoirs_press_head_od:
                    pressure_head = qepanet_reservoirs_press_head_od[ndID[p]]

                feature.setAttributes(
                    [ndID[p], reservoirs_elev[i] - delta_z - pressure_head, delta_z, pressure_head, ndPatID[p]])
                reservoirs_lay_dp.addFeatures([feature])

        return {Junction.section_name: junctions_lay,
                Reservoir.section_name: reservoirs_lay,
                Tank.section_name: tanks_lay,
                Pipe.section_name: pipes_lay,
                Pump.section_name: pumps_lay,
                Valve.section_name: valves_lay}

    def update_mixing(self, mixing):
        # TODO
        pass

    def update_reactions(self, reactions):
        # TODO
        pass

    def update_sources(self, sources):
        # TODO
        pass

    def update_rules(self, rules):
        # TODO
        pass

    def update_quality(self, quality):
        # TODO
        pass

    def update_curves(self):
        InpFile.read_curves(self.params, self.inp_path)

    def update_patterns(self):
        InpFile.read_patterns(self.params, self.inp_path)

    def update_controls(self, controls):
        # TODO
        pass

    def update_demands(self, demands):
        # TODO
        pass

    def update_energy(self, energy):
        for e in energy:
            if e[1].upper() == 'EFFICIENCY':
                self.params.energy.pump_efficiency = e[2]
            elif e[1].upper() == 'PRICE':
                self.params.energy.energy_price = e[2]
            elif e[1].upper() == 'CHARGE':
                self.params.energy.demand_charge = e[2]
        # TODO: price pattern and single pumps

    def update_opt_reactions(self, opt_reactions):
        for r in opt_reactions:
            if r[0].upper() == 'ORDER':
                if r[1].upper() == 'BULK':
                    self.params.reactions.order_bulk = r[2]
                elif r[1].upper() == 'TANK':
                    self.params.reactions.order_tank = r[2]
                elif r[1].upper() == 'WALL':
                    self.params.reactions.order_wall = r[2]
            elif r[0].upper() == 'GLOBAL':
                if r[1].upper() == 'BULK':
                    self.params.reactions.global_bulk = r[2]
                elif r[1].upper() == 'WALL':
                    self.params.reactions.global_wall = r[2]
            elif r[0].upper() == 'LIMITING' and r[1].upper() == 'POTENTIAL':
                    self.params.reactions.limiting_potential = r[2]
            elif r[0].upper() == 'ROUGHNESS' and r[1].upper() == 'CORRELATION':
                    self.params.reactions.roughness_corr = r[2]

    def update_times(self, times):
        for t in times:
            if t[0].upper() == 'DURATION':
                self.params.times.duration = self.hour_from_text(t[1])
            elif t[0].upper() == 'HYDRAULIC' and t[1].upper() == 'TIMESTAMP':
                self.params.times.hydraulic_timestamp = self.hour_from_text(t[2])
            elif t[0].upper() == 'QUALITY' and t[1].upper() == 'TIMESTAMP':
                self.params.times.quality_timestamp = self.hour_from_text(t[2])
            elif t[0].upper() == 'PATTERN' and t[1].upper() == 'TIMESTAMP':
                self.params.times.pattern_timestamp = self.hour_from_text(t[2])
            elif t[0].upper() == 'PATTERN' and t[1].upper() == 'START':
                self.params.times.pattern_start = self.hour_from_text(t[2])
            elif t[0].upper() == 'REPORT' and t[1].upper() == 'TIMESTAMP':
                self.params.times.report_timestamp = self.hour_from_text(t[2])
            elif t[0].upper() == 'REPORT' and t[1].upper() == 'START':
                self.params.times.report_start = self.hour_from_text(t[2])
            elif t[0].upper() == 'START' and t[1].upper() == 'CLOCKTIME':
                time = self.hour_from_text(t[2])
                if len(t) > 3 and t[3].upper() == 'PM':
                    time += 12
                self.params.times.clocktime_start = time
            elif t[0].upper() == 'STATISTIC':
                for key, text in Times.stats_text.iteritems():
                    if t[1].upper() == text.upper():
                        self.params.times.statistic = key
                        break

    def update_report(self, report):
        for r in report:
            if r[0].upper() == 'STATUS':
                if r[1].upper() == 'YES':
                    self.params.report.status = Report.status_yes
                elif r[1].upper() == 'NO':
                    self.params.report.status = Report.status_no
                elif r[1].upper() == 'FULL':
                    self.params.report.status = Report.status_full
            elif r[0].upper() == 'SUMMARY':
                if r[1].upper() == 'YES':
                    self.params.report.summary = Report.summary_yes
                else:
                    self.params.report.summary = Report.summary_no
            elif r[0].upper() == 'PAGE':
                self.params.report.page_size = r[1]
            elif r[0].upper() == 'ENERGY':
                if r[1].upper() == 'YES':
                    self.params.report.energy = Report.energy_yes
                else:
                    self.params.report.energy = Report.energy_no
            elif r[0].upper() == 'NODES':
                if r[1].upper() == 'ALL':
                    self.params.report.nodes = Report.nodes_all
                else:
                    self.params.report.nodes = Report.nodes_none
            elif r[0].upper() == 'LINKS':
                if r[1].upper() == 'ALL':
                    self.params.report.links = Report.links_all
                else:
                    self.params.report.links = Report.links_none

    def update_options(self, options):
        for o in options:
            if o[0].upper() == 'UNITS':

                if o[1].upper() in Options.units_flow[Options.unit_sys_si]:
                    self.params.options.units = Options.unit_sys_si
                elif o[1].upper() in Options.units_flow[Options.unit_sys_us]:
                    self.params.options.units = Options.unit_sys_us

                self.params.options.units_flow = o[1].upper() # TODO: Check
            elif o[0].upper() == 'HEADLOSS':
                self.params.options.headloss = o[1].upper()
            elif o[0].upper() == 'SPECIFIC' and o[1].upper() == 'GRAVITY':
                self.params.options.spec_gravity = float(o[2])
            elif o[0].upper() == 'VISCOSITY':
                self.params.options.viscosity = float(o[1])
            elif o[0].upper() == 'TRIALS':
                self.params.options.trials = int(o[1])
            elif o[0].upper() == 'ACCURACY':
                self.params.options.accuracy = float(o[1])
            elif o[0].upper() == 'MAXCHECK':
                pass
            elif o[0].upper() == 'DAMPLIMIT':
                pass
            elif o[0].upper() == 'UNBALANCED':
                unbalanced = Unbalanced()
                if o[1].upper() == 'CONTINUE':
                    trials = int(o[2])
                    unbalanced.unbalanced = Unbalanced.unb_continue
                    unbalanced.trials = trials
                else:
                    unbalanced.unbalanced = Unbalanced.unb_stop
                self.params.options.unbalanced = unbalanced
            elif o[0].upper() == 'PATTERN':
                if o[1] in self.params.patterns:
                    self.params.options.pattern = self.params.patterns[o[1]]
                else:
                    self.params.options.pattern = None
            elif o[0].upper() == 'DEMAND' and o[1].upper() == 'MULTIPLIER':
                self.params.options.demand_mult = float(o[2])
            elif o[0].upper() == 'EMITTER' and o[2].upper() == 'EXPONENT':
                self.params.options.units = float(o[2])
            elif o[0].upper() == 'QUALITY':
                quality = Quality()
                if o[1].upper() == 'NONE':
                    quality.parameter = Quality.quality_none
                elif o[1].upper() == 'AGE':
                    quality.parameter = Quality.quality_age
                elif o[1].upper() == 'TRACE':
                    quality.parameter = Quality.quality_trace
                else:
                    quality.parameter = Quality.quality_chemical
                    quality.quality_chemical = o[1]

                    units = o[2]
                    if units == 'mg/L':
                        quality.mass_units = Quality.quality_units_mgl
                    elif units == 'ug/L':
                        quality.mass_units = Quality.quality_units_ugl

                self.params.options.quality = quality

            # elif o[0].upper() == '':
            #     self.params.options.units = ?
            # elif o[0].upper() == '':
            #     self.params.options.units = ?
            # elif o[0].upper() == '':
            #     self.params.options.units = ?

    def hour_from_text(self, hhmm):

        hrs_min = hhmm.split(':')

        if hrs_min[0]:
            hrs = int(hrs_min[0])
            mins = 0
        if len(hrs_min) > 1 and hrs_min[1]:
            mins = int(hrs_min[1])

        hour = Hour(hrs, mins)

        return hour

    def read_section(self, section_name):

        section_name = '[' + section_name + ']'

        section_started = False
        start_line = None
        end_line = None
        for l in range(len(self.lines)):
            if section_name.upper() in self.lines[l].upper():
                section_started = True
                start_line = l + 1
                continue
            if self.lines[l].startswith('[') and section_started:
                end_line = l - 1
                break

        if start_line is None:
            return None

        if end_line is None:
            end_line = len(self.lines)

        return self.lines[start_line:end_line]

    def read_qepanet_junctions(self):

        lines = self.read_section(QJunction.section_name)

        junctions_elevcorr_od = OrderedDict()
        if lines is not None:
            for line in lines:
                if line.strip().startswith(';'):
                    continue
                words = line.split()
                if len(words) > 1:
                    junctions_elevcorr_od[words[0].strip()] = float(words[1].strip())

        return junctions_elevcorr_od

    def read_qepanet_reservoirs(self):

        lines = self.read_section(QReservoir.section_name)
        reservoirs_elevcorr_od = OrderedDict()
        reservoirs_press_heads_od = OrderedDict()
        if lines is not None:
            for line in lines:
                if line.strip().startswith(';'):
                    continue
                words = line.split()
                if len(words) > 1:
                    reservoirs_elevcorr_od[words[0].strip()] = float(words[1].strip())
                if len(words) > 2:
                    reservoirs_press_heads_od[words[0].strip()] = float(words[2].strip())

        return reservoirs_elevcorr_od, reservoirs_press_heads_od

    def read_qepanet_tanks(self):

        lines = self.read_section(QTank.section_name)
        tanks_elevcorr_od = OrderedDict()
        if lines is not None:
            for line in lines:
                if line.strip().startswith(';'):
                    continue
                words = line.split()
                if len(words) > 1:
                    tanks_elevcorr_od[words[0].strip()] = float(words[1].strip())

        return tanks_elevcorr_od

    def read_qepanet_pipes(self):

        lines = self.read_section(QPipe.section_name)
        pipes_material_od = OrderedDict()
        if lines is not None:
            for line in lines:
                if line.strip().startswith(';'):
                    continue
                words = line.split()
                if len(words) > 1:
                    pipes_material_od[words[0].strip()] = words[1].strip()

        return pipes_material_od

    def read_qepanet_vertices(self):

        lines = self.read_section(QVertices.section_name)
        vertices_zs_od = OrderedDict()
        if lines is not None:
            for line in lines:
                if line.strip().startswith(';'):
                    continue
                words = line.split()
                if len(words) > 1:
                    vertices_zs_od[words[0].strip()] = float(words[1].strip())

        return vertices_zs_od


# ir = InpReader('D:/temp/5.inp')
# print ir.read_qepanet_tanks()