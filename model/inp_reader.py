# Modified from https://plugins.qgis.org/plugins/ImportEpanetInpFiles/
# (C)Marios Kyriakou 2016
# University of Cyprus, KIOS Research Center for Intelligent Systems and Networks

from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import QVariant
# from tools.data_stores import MemoryDS
from network import *

import readEpanetFile as d
from inp_writer import InpFile
from ..tools.parameters import Parameters
from .options_report import Options, Unbalanced, Quality, Report

class InpReader2:

    def __init__(self):
        self.params = None

    def read(self, inp_path, params):

        self.params = params

        d.LoadFile(inp_path)
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
        status = d.getStatusSection()
        demands = d.getDemandsSection()
        energy = d.getEnergySection()
        opt_reactions = d.getReactionsOptionsSection()
        times = d.getTimesSection()
        report = d.getReportSection()
        options = d.getOptionsSection()

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
        if emitters:
            self.update_emitters(emitters)
        if status:
            self.update_status(status)
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
        if d.getBinNodeJunctionCount() > 0:
            # Write Junction Shapefile
            posJunctions = QgsVectorLayer('Point', 'Junctions', 'memory')
            prJunctions = posJunctions.dataProvider()
            prJunctions.addAttributes(Junction.fields)
            posJunctions.updateFields()

            ndEle = d.getBinNodeJunctionElevations()
            ndBaseD = d.getBinNodeBaseDemands()
            ndID = d.getBinNodeNameID()
            ndPatID = d.getBinNodeDemandPatternID()

        # Get data of Pipes
        # Write shapefile pipe
        if links_count > 0:

            # Pipes
            posPipes = QgsVectorLayer('LineString', 'Pipes', 'memory')
            prPipe = posPipes.dataProvider()
            prPipe.addAttributes(Pipe.fields)
            posPipes.updateFields()

            # Pumps
            posPumps = QgsVectorLayer('LineString', 'Pumps', 'memory')
            prPump = posPumps.dataProvider()
            prPump.addAttributes(Pump.fields)
            posPumps.updateFields()

            # Valves
            posValves = QgsVectorLayer('LineString', 'Valves', 'memory')
            prValve = posValves.dataProvider()
            prValve.addAttributes(Valve.fields)
            posValves.updateFields()

            pIndex = d.getBinLinkPumpIndex()
            vIndex = d.getBinLinkValveIndex()
            ndlConn = d.getBinNodesConnectingLinksID()
            x1 = [];
            x2 = [];
            y1 = [];
            y2 = []
            stat = d.getBinLinkInitialStatus()

            kk = 0;
            ch = 0
            linkID = d.getBinLinkNameID()
            linkLengths = d.getBinLinkLength()
            linkDiameters = d.getBinLinkDiameter()
            linkRough = d.getBinLinkRoughnessCoeff()
            linkMinorloss = d.getBinLinkMinorLossCoeff()

        # Write Tank Shapefile and get tank data
        if d.getBinNodeTankCount() > 0:
            posTanks = QgsVectorLayer('Point', 'Tanks', 'memory')
            prTank = posTanks.dataProvider()

            prTank.addAttributes([QgsField('id', QVariant.String),
                                  QgsField('elevation', QVariant.Double),
                                  QgsField('initiallev', QVariant.Double),
                                  QgsField('minimumlev', QVariant.Double),
                                  QgsField('maximumlev', QVariant.Double),
                                  QgsField('diameter', QVariant.Double),
                                  QgsField('minimumvol', QVariant.Double),
                                  QgsField('volumecurv', QVariant.Double)])

            posTanks.updateFields()

            # posTank.startEditing()

            ndTankelevation = d.getBinNodeTankElevations()
            initiallev = d.getBinNodeTankInitialLevel()
            minimumlev = d.getBinNodeTankMinimumWaterLevel()
            maximumlev = d.getBinNodeTankMaximumWaterLevel()
            diameter = d.getBinNodeTankDiameter()
            minimumvol = d.getBinNodeTankMinimumWaterVolume()
            volumecurv = d.getBinNodeTankVolumeCurveID()
            ndTankID = d.getBinNodeTankNameID()

        # Write Reservoir Shapefile
        if d.getBinNodeReservoirCount() > 0:
            posReservoirs = QgsVectorLayer('Point', 'Reservoirs', 'memory')
            prReservoirs = posReservoirs.dataProvider()

            prReservoirs.addAttributes(Reservoir.fields)

            posReservoirs.updateFields()

            head = d.getBinNodeReservoirElevations()
            # posReservoirs.startEditing()

        vvLink = 68
        bbLink = 1

        vPos = 0
        pPos = 0

        for i in range(ss):
            if i == ss / vvLink and vvLink > -1:
                vvLink = vvLink - 1
                bbLink = bbLink + 1

            if i < d.getBinNodeJunctionCount():
                featJ = QgsFeature()
                point = QgsPoint(float(x[i]), float(y[i]))
                featJ.setGeometry(QgsGeometry.fromPoint(point))
                featJ.setAttributes([ndID[i], ndEle[i], ndPatID[i], ndBaseD[i]])
                prJunctions.addFeatures([featJ])

            if i < links_count:
                if len(stat) == i:
                    ch = 1
                if ch == 1:
                    stat.append('OPEN')

                x1.append(x[ndID.index(d.getBinLinkFromNode()[i])])
                y1.append(y[ndID.index(d.getBinLinkFromNode()[i])])
                x2.append(x[ndID.index(d.getBinLinkToNode()[i])])
                y2.append(y[ndID.index(d.getBinLinkToNode()[i])])

                if i in pIndex:
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
                    Curve = []
                    power = []
                    pattern = []
                    pumpNameIDPower = d.getBinLinkPumpNameIDPower()

                    if len(pumpNameIDPower) > 0:
                        for uu in range(0, len(pumpNameIDPower)):
                            if pumpNameIDPower[uu] == pumpID[i]:
                                power = chPowerPump[uu]
                    if len(patternsIDs) > 0:
                        for uu in range(0, len(ppatt)):
                            if ppatt[uu] == pumpID[i]:
                                pattern = patternsIDs[uu]

                    if d.getBinCurveCount() > 0 and len(pumpNameIDPower) == 0:
                        curveXY = d.getBinCurvesXY()
                        curvesID = d.getBinCurvesNameID()
                        for uu in range(0, len(curveXY)):
                            if curvesID[uu] == cheadpump[pPos]:
                                Head.append(str(curveXY[uu][0]))
                                Flow.append(str(curveXY[uu][1]))
                        Curve = d.getBinLinkPumpCurveNameID()[pPos]

                    featPump = QgsFeature()
                    featPump.setGeometry(QgsGeometry.fromPolyline([point1, point2]))

                    Head = ' '.join(Head)
                    Flow = ' '.join(Flow)
                    if Head == []:
                        Head = 'NULL'
                    if Flow == []:
                        Flow = 'NULL'
                    if Curve == []:
                        Curve = 'NULL'
                    if power == []:
                        power = 'NULL'
                    if pattern == []:
                        pattern = 'NULL'
                    featPump.setAttributes([linkID[pPos], Head, Flow, power, pattern, Curve])
                    prPump.addFeatures([featPump])

                elif i in vIndex:
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
                    prValve.addFeatures([featValve])

                    vPos += 1

                else:
                    # Pipe
                    point1 = QgsPoint(float(x1[i]), float(y1[i]))
                    point2 = QgsPoint(float(x2[i]), float(y2[i]))
                    if vertx[i] != []:
                        parts = []
                        parts.append(point1)
                        for mm in range(len(vertxyFinal[kk])):
                            a = vertxyFinal[kk][mm]
                            parts.append(QgsPoint(a[0], a[1]))
                        parts.append(point2)
                        featPipe = QgsFeature()
                        featPipe.setGeometry((QgsGeometry.fromPolyline(parts)))
                        kk += 1
                    else:
                        featPipe = QgsFeature()
                        point1 = QgsPoint(float(x1[i]), float(y1[i]))
                        point2 = QgsPoint(float(x2[i]), float(y2[i]))
                        featPipe.setGeometry(QgsGeometry.fromPolyline([point1, point2]))

                    featPipe.setAttributes(
                        [linkID[i], linkLengths[i], linkDiameters[i], stat[i],
                         linkRough[i], linkMinorloss[i]])
                    prPipe.addFeatures([featPipe])

            if i < d.getBinNodeTankCount():
                p = d.getBinNodeTankIndex()[i] - 1
                featTank = QgsFeature()
                point = QgsPoint(float(x[p]), float(y[p]))
                featTank.setGeometry(QgsGeometry.fromPoint(point))
                featTank.setAttributes(
                    [ndTankID[i], ndTankelevation[i], initiallev[i], minimumlev[i], maximumlev[i], diameter[i],
                     minimumvol[i], volumecurv[i]])
                prTank.addFeatures([featTank])

            if i < d.getBinNodeReservoirCount():
                p = d.getBinNodeReservoirIndex()[i] - 1
                feature = QgsFeature()
                point = QgsPoint(float(x[p]), float(y[p]))
                feature.setGeometry(QgsGeometry.fromPoint(point))
                feature.setAttributes([ndID[p], head[i]])
                prReservoirs.addFeatures([feature])

        return {Junction.section_name: posJunctions,
                Reservoir.section_name: posReservoirs,
                Tank.section_name: posTanks,
                Pipe.section_name: posPipes,
                Pump.section_name: posPumps,
                Valve.section_name: posValves}

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
        InpFile.read_curves(self.params)

    def update_patterns(self):
        InpFile.read_patterns(self.params)

    def update_controls(self, controls):
        # TODO
        pass

    def update_emitters(self, emitters):
        # TODO
        pass

    def update_status(self, status):
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
                self.params.times.duration = self.timestamp_from_text(t[1])
            elif t[0].upper() == 'HYDRAULIC' and t[1].upper() == 'TIMESTAMP':
                self.params.times.hydraulic_timestamp = self.timestamp_from_text(t[2])
            elif t[0].upper() == 'QUALITY' and t[1].upper() == 'TIMESTAMP':
                self.params.times.quality_timestamp = self.timestamp_from_text(t[2])
            elif t[0].upper() == 'PATTERN' and t[1].upper() == 'TIMESTAMP':
                self.params.times.pattern_timestamp = self.timestamp_from_text(t[2])
            elif t[0].upper() == 'PATTERN' and t[1].upper() == 'START':
                self.params.times.pattern_start = self.timestamp_from_text(t[2])
            elif t[0].upper() == 'REPORT' and t[1].upper() == 'TIMESTAMP':
                self.params.times.report_timestamp = self.timestamp_from_text(t[2])
            elif t[0].upper() == 'REPORT' and t[1].upper() == 'START':
                self.params.times.report_start = self.timestamp_from_text(t[2])
            elif t[0].upper() == 'START' and t[1].upper() == 'CLOCKTIME':
                time = self.timestamp_from_text(t[2])
                if t[3].upper() == 'PM':
                    time += 12
                self.params.times.clocktime_start = time
            elif t[0].upper() == 'STATISTIC':
                self.params.times.statistic = t[1]

    def update_report(self, report):
        for r in report:
            if r[0].upper() == 'STATUS':
                self.params.report.status = r[1]
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
                if o[1].upper == 'CONTINUE':
                    trials = int(o[2])
                    unbalanced.unbalanced = Unbalanced.unb_continue
                    unbalanced.trials = trials
                else:
                    unbalanced.unbalanced = Unbalanced.unb_stop
                self.params.options.unbalanced = unbalanced
            elif o[0].upper() == 'PATTERN':
                self.params.options.pattern = o[1]
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

    def timestamp_from_text(self, hhmm):

        hrs_min = hhmm.split(':')

        if hrs_min[0]:
            hrs = float(hrs_min[0])
            mins = 0
        if len(hrs_min) > 1 and hrs_min[1]:
            mins = float(hrs_min[1])

        return hrs + mins / 60



# ir = InpReader2()
# ir.read('D:/temp/5.inp', None)
# ir.read('D:/temp/b.inp')