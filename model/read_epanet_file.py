import re
from network import *
from system_ops import *
from options_report import *

class InpReader:
    
    def __init__(self, inp_file_name):

        self.tags = []
        self.mm = self.read(inp_file_name)
    
    # def LoadFile(inp):
    #     # getPathPlugin = os.path.dirname(os.path.realpath(__file__))+"/"
    #     # inpname = getPathPlugin + inp
    #     inpname = inp
    # 
    # def BinUpdateClass(self):
    #     global mm
    #     mm = getBinInfo()
    #     return mm
    
    ## get Info
    def getBinNodeReservoirIndex(self):
        ind = range(self.getBinNodeJunctionCount() + 1, self.getBinNodeJunctionCount() + self.getBinNodeReservoirCount() + 1)
        return ind
    
    def getBinNodeTankIndex(self):
        ind = range(self.getBinNodeJunctionCount() + self.getBinNodeReservoirCount() + 1, self.getBinNodeCount() + 1)
        return ind
    
    def getBinNodeDemandPatternID(self):
        return self.mm[3]
    
    def getBinNodeJunctionCount(self):
        return self.mm[4]
    
    def getBinNodeReservoirCount(self):
        return self.mm[7]
    
    def getBinNodeIndex(self, id):
        nodeNameID = self.getBinNodeNameID()
        return nodeNameID.index(id)
    
    def getBinNodeNameID(self):
        return self.mm[0] + self.mm[5] + self.mm[8]
    
    def getBinNodeJunctionNameID(self):
        return self.mm[0]
    
    def getBinReservoirNameID(self):
        return self.mm[5]
    
    # def getBinNodeElevations(self):
    #     global mm
    #     nodeElevations=getBinNodeJunctionElevations()
    #     for i in range(len(mm[6])):
    #         nodeElevations.append(mm[6][i])#reservoirs
    #     for i in range(len(mm[6])):
    #         nodeElevations.append(mm[9][i])
    #     return nodeElevations
    
    def getBinNodeJunctionElevations(self):
        return self.mm[1]
    
    def getBinNodeReservoirElevations(self):
        return self.mm[6]
    
    def getBinNodeBaseDemands(self):
        return self.mm[2]
    
    # Tanks Info
    def getBinNodeTankNameID(self):
        return self.mm[8]
    
    def getBinNodeTankCount(self):
        return len(self.getBinNodeTankNameID())
    
    def getBinNodeTankElevations(self):
        return self.mm[9]
    
    def getBinNodeTankInitialLevel(self):
        return self.mm[10]
    
    def getBinNodeTankMinimumWaterLevel(self):
        return self.mm[11]
    
    def getBinNodeTankMaximumWaterLevel(self):
        return self.mm[12]
    
    def getBinNodeTankDiameter(self):
        return self.mm[13]
    
    def getBinNodeTankMinimumWaterVolume(self):
        return self.mm[14]
    
    def getBinNodeTankVolumeCurveID(self):
        return self.mm[35]
    
    # Get Links Info
    def getBinLinkPumpIndex(self):
        ind = []
        for i in range(self.getBinLinkPipeCount() + 1, self.getBinLinkPipeCount() + self.getBinLinkPumpCount() + 1):
            ind.append(i - 1)
        return ind

    def getBinLinkValveIndex(self):
        ind = []
        for i in range(self.getBinLinkPipeCount() + self.getBinLinkPumpCount() + 1, self.getBinLinkCount() + 1):
            ind.append(i - 1)
        return ind

    def getBinLinkIndex(self, id):
        linkNameID = self.getBinLinkNameID()
        return linkNameID.index(id)

    def getBinLinkNameID(self):
        return self.mm[15] + self.mm[22] + self.mm[27]

    def getBinLinkLength(self):
        ll = self.getBinLinkPipeLengths()
        for i in range(self.getBinLinkPipeCount() + 1, self.getBinLinkCount() + 1):
            ll.append(0)
        return ll

    def getBinLinkDiameter(self):
        ll = self.getBinLinkPipeDiameters()
        vld = self.getBinLinkValveDiameters()
        for i in range(self.getBinLinkPipeCount() + 1, self.getBinLinkPipeCount() + self.getBinLinkPumpCount() + 1):
            ll.append(0)
        for i in range(self.getBinLinkValveCount()):
            ll.append(vld[i])
        return ll
    
    
    def getBinLinkRoughnessCoeff(self):
        ll = self.getBinLinkPipeRoughness()
        for i in range(self.getBinLinkPipeCount() + 1, self.getBinLinkCount() + 1):
            ll.append(0)
        return ll
    
    
    def getBinLinkMinorLossCoeff(self):
        ll = self.getBinLinkPipeMinorLoss()
        vld = self.getBinLinkValveMinorLoss()
        for i in range(self.getBinLinkPipeCount() + 1, self.getBinLinkPipeCount() + self.getBinLinkPumpCount() + 1):
            ll.append(0)
        for i in range(self.getBinLinkValveCount()):
            ll.append(vld[i])
        return ll
    
    def getBinLinkPipeCount(self):
        return len(self.getBinLinkPipeNameID())
    
    def getBinLinkPipeNameID(self):
        return self.mm[15]
    
    
    def getBinLinkFromNode(self):
        return self.mm[16]
    
    def getBinLinkToNode(self):
        return self.mm[17]
    
    def getBinLinkPipeLengths(self):
        return self.mm[18]
    
    def getBinLinkPipeDiameters(self):
        return self.mm[19]
    
    def getBinLinkPipeRoughness(self):
        return self.mm[20]
    
    def getBinLinkPipeMinorLoss(self):
        return self.mm[21]
    
    # Get Pumps Info
    def getBinLinkPumpCount(self):
        return len(self.getBinLinkPumpNameID())
    
    def getBinLinkPumpNameID(self):
        return self.mm[22]
    
    def getBinLinkPumpPatterns(self):
        return self.mm[23]
    
    def getBinLinkPumpCurveNameID(self):
        return self.mm[24]
    
    def getBinLinkPumpPower(self):
        return self.mm[25]
    
    def getBinLinkPumpNameIDPower(self):
        return self.mm[26]
    
    def getBinLinkPumpSpeed(self):
        return self.mm[38]
    
    def getBinLinkPumpPatternsPumpID(self):
        return self.mm[39]
    
    def getBinLinkPumpSpeedID(self):
        return self.mm[62]
    
    # Get Valves Info
    def getBinLinkValveCount(self):
        return len(self.getBinLinkValveNameID())
    
    def getBinLinkValveNameID(self):
        return self.mm[27]
    
    def getBinLinkValveDiameters(self):
        return self.mm[28]
    
    def getBinLinkValveType(self):
        return self.mm[29]
    
    def getBinLinkValveSetting(self):
        return self.mm[30]
    
    def getBinLinkValveMinorLoss(self):
        return self.mm[31]
    
    def getBinNodesConnectingLinksID(self):
        return [self.mm[16], self.mm[17]]

    def getBinNodesConnectingLinksIndex(self):
        NodesConnectingLinksID = self.getBinNodesConnectingLinksID()
        nodeInd = []
        for i in range(self.getBinLinkCount()):
            nodeInd.append([self.getBinNodeIndex(NodesConnectingLinksID[0][i]), self.getBinNodeIndex(NodesConnectingLinksID[1][i])])
        return nodeInd
    
    def getBinLinkCount(self):
        return self.getBinLinkPipeCount() + self.getBinLinkPumpCount() + self.getBinLinkValveCount()

    def getBinNodeCount(self):
        return self.getBinNodeJunctionCount() + self.getBinNodeReservoirCount() + self.getBinNodeTankCount()
    
    # Status
    def getBinLinkInitialStatus(self):
        return self.mm[32]

    def getBinLinkInitialStatusNameID(self):
        return self.mm[33]
    
    # Curves
    def getBinCurvesNameID(self):
        return self.mm[36]
    
    def getBinCurvesXY(self):
        return self.mm[37]
    
    def getBinCurveCount(self):
        return len(set(self.mm[36]))
    
    def getDemandsSection(self):
        return self.mm[44]
    
    def getStatusSection(self):
        return self.mm[45]
    
    def getEmittersSection(self):
        return self.mm[46]
    
    def getControlsSection(self):
        return self.mm[47]
    
    def getPatternsSection(self):
        return self.mm[48]
    
    def getCurvesSection(self):
        return self.mm[49], self.mm[50]
    
    def getQualitySection(self):
        return self.mm[51]
    
    def getRulesSection(self):
        return self.mm[52]
    
    def getSourcesSection(self):
        return self.mm[53]
    
    def getEnergySection(self):
        return self.mm[54]
    
    def getReactionsSection(self):
        return self.mm[55]
    
    def getReactionsOptionsSection(self):
        return self.mm[56]
    
    def getMixingSection(self):
        return self.mm[57]

    def getTimesSection(self):
        return self.mm[58]
    
    def getOptionsSection(self):
        return self.mm[59]
    
    def getReportSection(self):
        return self.mm[60]
    
    def getLabelsSection(self):
        return self.mm[61]
    
    # Descriptions
    def get_junctions_desc(self):
        return self.mm[63]
    
    def get_reservoirs_desc(self):
        return self.mm[64]
    
    def get_tanks_desc(self):
        return self.mm[65]
    
    def get_nodes_desc(self):
        return self.mm[63] + self.mm[64] + self.mm[65]
    
    def get_pipes_desc(self):
        return self.mm[66]
    
    def get_pumps_desc(self):
        return self.mm[67]
    
    def get_valves_desc(self):
        return self.mm[68]
    
    def get_links_desc(self):
        return self.mm[66] + self.mm[67] + self.mm[68]
    
    def get_tags(self):
        return self.tags
    
    # Get all info
    def read(self, inp_file_name):
        # file = open(inpname, 'r')
    
        nodeJunctionNameID = []
        nodeJunctionElevations = []
        nodeJunctionBaseDemands = []
        nodePatternNameID = []
        nodeReservoirNameID = []
        nodeReservoirElevations = []
    
        BinNodeTankNameID = []
        BinNodeTankElevation = []
        BinNodeTankInitLevel = []
        BinNodeTankMinLevel = []
        BinNodeTankMaxLevel = []
        BinNodeTankDiameter = []
        BinNodeTankMinVol = []
        BinNodeTankVolumeCurveID = []
    
        BinLinkPipeNameID = []
        BinLinkFromNode = []
        BinLinkToNode = []
        BinLinkPipeLengths = []
        BinLinkPipeDiameters = []
        BinLinkPipeRoughness = []
        BinLinkPipeMinorLoss = []
    
        BinLinkPumpPatterns = []
        BinLinkPumpCurveNameID = []
        BinLinkPumpPower = []
        BinLinkPumpNameIDPower = []
        BinLinkPumpNameID = []
        BinLinkPumpSpeedID = []
        BinLinkPumpSpeed = []
        BinLinkPumpPatternsPumpID = []
    
        junctions_desc = []
        reservoirs_desc = []
        tanks_desc = []
        pipes_desc = []
        pumps_desc = []
        valves_desc = []
        tags = []
    
        BinLinkValveNameID = []
        BinLinkValveDiameters = []
        BinLinkValveType = []
        BinLinkValveSetting = []
        BinLinkValveMinorLoss = []
    
        BinLinkInitialStatus = []
        BinLinkInitialStatusNameID = []
        BincountStatuslines = []
        linkNameID = []
    
        BinCurvesNameID = []
        BinCurvesXY = []
    
        # Sections
        demandsSection = []
        statusSection = []
        emittersSection = []
        controlsSection = []
        patternsSection = []
        curvesSection = []
        curvesSectionType = []
        qualitySection = []
        rulesSection = []
        rules = []
        sourcesSection = []
        energySection = []
        reactionsSection = []
        reactionsOptionSection = []
        mixingSection = []
        timesSection = []
        optionsSection = []
        reportSection = []
        labelsSection = []
    
        # s1 = file.readline()
        num = 13
        sec = [0] * num
        x = []
        y = []
        # Create a list.
        vertx = []
        verty = []
        # Append empty lists in first two indexes.
        sec2 = [0] * num
        ch1 = 0
        ch = 1
        section_name = ''
    
        with open(inp_file_name) as openfileobject:
            for s1 in openfileobject:
    
                ok = 0
                if "[END]" in s1:
    
                    # file.close()
                    return [nodeJunctionNameID,  # 0
                            nodeJunctionElevations,  # 1
                            nodeJunctionBaseDemands,  # 2
                            nodePatternNameID,  # 3
                            len(nodeJunctionNameID),  # 4
                            nodeReservoirNameID,  # 5
                            nodeReservoirElevations,  # 6
                            len(nodeReservoirNameID),  # 7
                            BinNodeTankNameID,  # 8
                            BinNodeTankElevation,  # 9
                            BinNodeTankInitLevel,  # 10
                            BinNodeTankMinLevel,  # 11
                            BinNodeTankMaxLevel,  # 12
                            BinNodeTankDiameter,  # 13
                            BinNodeTankMinVol,  # 14
                            BinLinkPipeNameID, BinLinkFromNode, BinLinkToNode, BinLinkPipeLengths, BinLinkPipeDiameters,
                            BinLinkPipeRoughness, BinLinkPipeMinorLoss,  # 15#16#17#18#19#20#21
                            BinLinkPumpNameID, BinLinkPumpPatterns, BinLinkPumpCurveNameID, BinLinkPumpPower,
                            BinLinkPumpNameIDPower,  # 22#23#24#25#26
                            BinLinkValveNameID, BinLinkValveDiameters, BinLinkValveType, BinLinkValveSetting,
                            BinLinkValveMinorLoss,  # 27#28#29#30#31
                            BinLinkInitialStatus, BinLinkInitialStatusNameID, BincountStatuslines, BinNodeTankVolumeCurveID,
                            # 32#33#34#35
                            BinCurvesNameID, BinCurvesXY, BinLinkPumpSpeed, BinLinkPumpPatternsPumpID,  # 36#37#38#39
                            x, y, vertx, verty,  # 40#41#42#43
                            demandsSection, statusSection, emittersSection, controlsSection, patternsSection, curvesSection,
                            curvesSectionType,  # 44
                            qualitySection,  # 45
                            rulesSection,  # 46
                            sourcesSection,  # 47
                            energySection,   # 48
                            reactionsSection,  #50
                            reactionsOptionSection,
                            mixingSection,  # 57
                            timesSection,  # 58
                            optionsSection,  # 59
                            reportSection,  # 60
                            labelsSection,  # 61
                            BinLinkPumpSpeedID,  # 62
                            junctions_desc,   # 63
                            reservoirs_desc,   # 64
                            tanks_desc,   # 65
                            pipes_desc,  # 66
                            pumps_desc,  # 67
                            valves_desc,  # 68
                            ]
    
                elif "[JUNCTIONS]" in s1:
                    sec[0] = 1
                    section_name = Junction.section_name
                    continue
                elif "[RESERVOIRS]" in s1:
                    sec = [0] * num
                    sec[1] = 1
                    section_name = Reservoir.section_name
                    continue
                elif "[TANKS]" in s1:
                    sec = [0] * num
                    sec[2] = 1
                    section_name = Tank.section_name
                    continue
                elif "[PIPES]" in s1:
                    sec = [0] * num
                    sec[3] = 1
                    section_name = Pipe.section_name
                    continue
                elif "[PUMPS]" in s1:
                    sec = [0] * num
                    sec[4] = 1
                    section_name = Pump.section_name
                    continue
                elif "[VALVES]" in s1:
                    sec = [0] * num
                    sec[5] = 1
                    section_name = Valve.section_name
                    continue
                if "[STATUS]" in s1:
                    sec = [0] * num
                    sec2 = [0] * num
                    sec[7] = 1
                    # s1 = file.readline()
                    for i in range(0, len(BinLinkPipeNameID) + len(BinLinkPumpNameID) + len(BinLinkValveNameID)):
                        vertx.append([])
                        verty.append([])
                    linknameid = BinLinkPipeNameID + BinLinkPumpNameID + BinLinkValveNameID
                    section_name = Status.section_name
                    continue
                elif "[DEMANDS]" in s1:
                    sec = [0] * num
                    sec[8] = 1
                    section_name = Demand.section_name
                    continue
                elif (
                    "[JUNCTIONS]" in s1 or "[RESERVOIRS]" in s1 or "[TANKS]" in s1 or "[PIPES]" in s1 or "[PUMPS]" in s1 or "[VALVES]" in s1):
                    ok = 1
                elif "[TAGS]" in s1 and ok == 0:
                    sec = [0] * num
                    section_name = Tag.section_name
                    continue
                elif "[PATTERNS]" in s1:
                    sec = [0] * num
                    sec[6] = 1
                    section_name = Pattern.section_name
                    continue
                elif "[CURVES]" in s1:
                    sec = [0] * num
                    sec[9] = 1
                    section_name = Curve.section_name
                    continue
                elif "[CONTROLS]" in s1:
                    sec = [0] * num
                    sec[10] = 1
                    section_name = Control.section_name
                    continue
                elif "[COORDINATES]" in s1:
                    sec2 = [0] * num
                    sec2[0] = 1
                    section_name = Coordinate.section_name
                    continue
                elif "[VERTICES]" in s1:
                    sec2 = [0] * num
                    sec2[1] = 1
                    section_name = Vertex.section_name
                    continue
                elif "[LABELS]" in s1:
                    sec2 = [0] * num
                    sec2[12] = 1
                    section_name = Label.section_name
                    continue
                elif "[EMITTERS]" in s1:
                    sec2 = [0] * num
                    sec2[2] = 1
                    section_name = Emitter.section_name
                    continue
                elif "[RULES]" in s1:
                    sec = [0] * num
                    sec2 = [0] * num
                    sec2[3] = 1
                    section_name = Rule.section_name
                    continue
                elif "[ENERGY]" in s1:
                    sec2 = [0] * num
                    sec2[6] = 1
                    if rules != []:
                        rulesSection.append(rules)
                    section_name = Energy.section_name
                    continue
                elif "[QUALITY]" in s1:
                    sec2 = [0] * num
                    sec = [0] * num
                    sec2[4] = 1
                    section_name = Quality.section_name
                    continue
                elif "[SOURCES]" in s1:
                    sec2 = [0] * num
                    sec2[5] = 1
                    section_name = Source.section_name
                    continue
                elif "[REACTIONS]" in s1:
                    sec2 = [0] * num
                    sec2[7] = 1
                    section_name = Reaction.section_name
                    continue
                elif "[MIXING]" in s1:
                    sec2 = [0] * num
                    sec2[8] = 1
                    section_name = Mixing.section_name
                    continue
                elif "[TIMES]" in s1:
                    sec2 = [0] * num
                    sec2[9] = 1
                    section_name = Times.section_name
                    continue
                elif "[REPORT]" in s1:
                    sec2 = [0] * num
                    sec2[10] = 1
                    section_name = Report.section_name
                    continue
                elif "[OPTIONS]" in s1:
                    sec2 = [0] * num
                    sec2[11] = 1
                    section_name = Options.section_name
                    continue
                elif "[BACKDROP]" in s1:
                    sec2 = [0] * num
                    section_name = Backdrop.section_name
                    continue
                elif "[" in s1:
                    continue
    
                if s1.strip('\t ').startswith(';'):
                    continue
                mm, desc = self.read_line(s1)
    
                if not mm[0]:
                    continue
    
                # --------------------------------------------------------
                if sec[0] == 1:  # JUNCTIONS
    
                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
    
                            nodeJunctionNameID.append(mm[0].strip())
                            junctions_desc.append(desc)
                            nodeJunctionElevations.append(float(mm[1]))
    
                            node_jun_base_demand = 0
                            pattern = None
                            if len(mm) > 2 and mm[2].strip() != '':
                                node_jun_base_demand = float(mm[2])
                                # nodeJunctionBaseDemands.append(float(mm[2]))
                            if len(mm) > 3 and mm[3].strip() != '':
                                if mm[3][0] != ';':
                                    pattern = mm[3].strip()
    
                            nodeJunctionBaseDemands.append(node_jun_base_demand)
                            nodePatternNameID.append(pattern)
    
                if sec[1] == 1:  # RESERVOIRS
    
                    if not mm[0]:
                        continue
                    if len(mm) > 0:
                        if mm[0][0] == ';':
                            pass
                        else:
                            nodeReservoirNameID.append(mm[0].strip())
                            reservoirs_desc.append(desc)
                            nodeReservoirElevations.append(float(mm[1]))
                            if len(mm) > 2:
                                if mm[2][0] != ';':
                                    nodePatternNameID.append(mm[2].strip())
                                else:
                                    nodePatternNameID.append('')
                            else:
                                nodePatternNameID.append('')
    
                if sec[2] == 1:  # TANKS
    
                    if not mm[0]:
                        continue
                    if len(mm) > 0:
                        if mm[0][0] == ';':
                            pass
                        else:
                            BinNodeTankNameID.append(mm[0].strip())
                            tanks_desc.append(desc)
                            BinNodeTankElevation.append(float(mm[1]))
                            BinNodeTankInitLevel.append(float(mm[2]))
                            BinNodeTankMinLevel.append(float(mm[3]))
                            BinNodeTankMaxLevel.append(float(mm[4]))
                            BinNodeTankDiameter.append(float(mm[5]))
                            BinNodeTankMinVol.append(float(mm[6]))
                            nodePatternNameID.append('')
                            if len(mm) > 7:
                                if mm[7] and mm[7][0] != ';':
                                    BinNodeTankVolumeCurveID.append(mm[7].strip())
                                else:
                                    BinNodeTankVolumeCurveID.append('')
                            else:
                                BinNodeTankVolumeCurveID.append('')
    
                if sec[3] == 1:  # PIPES
    
                    if not mm[0]:
                        continue
                    if len(mm) > 0:
                        if mm[0][0] == ';':
                            pass
                        else:
                            linkNameID.append(mm[0].strip())
                            BinLinkPipeNameID.append(mm[0].strip())
                            pipes_desc.append(desc)
                            BinLinkFromNode.append(mm[1].strip())
                            BinLinkToNode.append(mm[2].strip())
                            BinLinkPipeLengths.append(float(mm[3]))
                            BinLinkPipeDiameters.append(float(mm[4]))
                            BinLinkPipeRoughness.append(float(mm[5]))
                            if len(mm) > 6:
                                BinLinkPipeMinorLoss.append(float(mm[6]))
                            else:
                                BinLinkPipeMinorLoss.append('')
                            if len(mm) > 7:
                                if mm[7][0] != ';':
                                    if mm[7] == 'Open':
                                        BinLinkInitialStatus.append('OPEN')
                                    else:
                                        BinLinkInitialStatus.append(mm[7])
    
                if sec[4] == 1:  # PUMPS
    
                    if not mm[0]:
                        continue
    
                    if mm[0][0] == ';':
                        pass
                    else:
                        linkNameID.append(mm[0].strip())
                        BinLinkPumpNameID.append(mm[0].strip())
                        pumps_desc.append(desc)
                        BinLinkFromNode.append(mm[1].strip())
                        BinLinkToNode.append(mm[2].strip())
    
                        keywords = ['POWER', 'HEAD', 'SPEED', 'PATTERN']
    
                        if len(mm) > 3:
                            for m in range(3, len(mm)-1):
                                if mm[m].upper() in keywords:
                                    value = None
                                    if m+1 < len(mm) and mm[m+1] not in keywords and mm[m+1].strip() != ';':
                                        value = mm[m+1]
    
                                    if mm[m].upper() == 'HEAD':
                                        BinLinkPumpCurveNameID.append(value)
                                    elif mm[m].upper() == 'POWER':
                                        power = 0
                                        if value is not None:
                                            power = float(value)
                                        BinLinkPumpPower.append(power)
                                        BinLinkPumpNameIDPower.append(mm[0].strip())
                                    elif mm[m].upper() == 'SPEED':
                                        speed = 0
                                        if value is not None:
                                            speed = float(value)
                                        BinLinkPumpSpeed.append(speed)
                                        BinLinkPumpSpeedID.append(mm[0].strip())
                                    elif mm[m].upper() == 'PATTERN':
                                        if value is not None:
                                            BinLinkPumpPatterns.append(value)
                                        BinLinkPumpPatternsPumpID.append(mm[0].strip())
    
                if sec[5] == 1:  # VALVES
    
                    if not mm[0]:
                        continue
    
                    if mm[0][0] == ';':
                        pass
                    else:
                        linkNameID.append(mm[0].strip())
                        valves_desc.append(desc)
                        BinLinkValveNameID.append(mm[0].strip())
                        BinLinkFromNode.append(mm[1].strip())
                        BinLinkToNode.append(mm[2].strip())
                        BinLinkValveDiameters.append(float(mm[3]))
                        BinLinkValveType.append(mm[4].strip())
                        BinLinkValveSetting.append(mm[5].strip())
                        if len(mm) > 6:
                            if mm[6][0] != ';':
                                BinLinkValveMinorLoss.append(float(mm[6]))
    
                if sec[6] == 1:  # PATTERNS
    
                    if not mm[0]:
                        continue
    
                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
                            patternsSection.append([mm[0], ' '.join(mm[1:])])
    
                if sec[7] == 1:  # STATUS
    
                    if not mm[0]:
                        continue
    
                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
                            statusSection.append(mm)
                            BinLinkInitialStatusNameID.append(mm[0])
                            if mm[1] == 'Open':
                                BinLinkInitialStatus.append('OPEN')
                            else:
                                BinLinkInitialStatus.append(mm[1])
                            BincountStatuslines.append(mm)
    
                if sec[8] == 1:  # DEMANDS
    
                    if not mm[0]:
                        continue
    
                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
                            nodeJunctionBaseDemands.append(float(mm[1]))
                            demandsSection.append(mm)
    
                if sec[9] == 1:  # CURVES
    
                    if not mm[0]:
                        continue
    
                    if len(mm) > 0:
                        if mm[0][0].strip() == ';':
                            if mm[0] == ';ID':
                                continue
                            elif ";PUMP:" in mm[0].upper():
                                curvesSectionType.append('PUMP')
                            elif ";EFFICIENCY:" in mm[0].upper():
                                curvesSectionType.append('EFFICIENCY')
                            elif ";VOLUME:" in mm[0].upper():
                                curvesSectionType.append('VOLUME')
                            elif ";HEADLOSS:" in mm[0].upper():
                                curvesSectionType.append('HEADLOSS')
                            else:
                                curvesSectionType.append('PUMP')
    
                        if mm[0][0].strip() != ';':
                            curvesSection.append(mm)
                            BinCurvesNameID.append(mm[0])
                            BinCurvesXY.append([float(mm[1]), float(mm[2])])
    
                if sec[10] == 1:  # CONTROLS
                    if "[" in s1:
                        continue
                    # mm = s1.split()
    
                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
                            controlsSection.append(' '.join(mm))
    
                if sec2[0] == 1:  # COORDINATES
                    if "[" in s1:
                        continue
                    # mm = s1.split()
    
                    if len(mm) > 2:
                        if mm[0][0] != ';':
                            x.append(float(mm[1]))
                            y.append(float(mm[2]))
    
                if sec2[1] == 1:  # VERTICES
                    if "[" in s1:
                        continue
                    # mm = s1.split()
    
                    if len(mm) > 2:
                        if mm[0][0] != ';':
                            linkIndex = linknameid.index(mm[0])
                            vertx[linkIndex].append(float(mm[1]))
                            verty[linkIndex].append(float(mm[2]))
    
                if sec2[2] == 1:  # EMITTERS
                    if "[" in s1:
                        continue
                    # mm = s1.split()
    
                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
                            emittersSection.append(mm)
    
                if sec2[3] == 1:  # RULES
                    if "[" in s1:
                        continue
                    # mm = s1.split()
    
                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
                            if "RULE" in mm[0].upper():
                                if rules != [] or ch == 0:
                                    rulesSection.append(rules)
                                    ch = 0
                                    rules = []
                                    rules.append([s1, mm])
                                else:
                                    rules.append([s1, mm])
                            else:
                                rules.append([s1, mm])
    
                if sec2[4] == 1:  # QUALITY
                    if "[" in s1:
                        continue
                    # mm = s1.split()
                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
                            qualitySection.append(mm)
    
                if sec2[5] == 1:  # SOURCES
                    if "[" in s1:
                        continue
                    # mm = s1.split()
                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
                            sourcesSection.append(mm)
    
                if sec2[6] == 1:  # ENERGY
                    if "[" in s1:
                        continue
                    # mm = s1.split()
    
                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
                            energySection.append(mm)
    
                if sec2[7] == 1:  # REACTIONS
                    if "[" in s1:
                        continue
                    # mm = s1.split()
                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
                            if ("ORDER" in mm[0].upper() and ch1 == 0) or ch1 == 1:
                                reactionsOptionSection.append(mm);
                                ch1 = 1
                            else:
                                reactionsSection.append(mm)
    
                if sec2[8] == 1:  # MIXING
                    if "[" in s1:
                        continue
                    # mm = s1.split()
                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
                            mixingSection.append(mm)
    
                if sec2[9] == 1:  # TIMES
                    if "[" in s1:
                        continue
                    # mm = s1.split()
                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
                            timesSection.append(mm)
    
                if sec2[10] == 1:  # REPORT
                    if "[" in s1:
                        continue
                    # mm = s1.split()
                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
                            reportSection.append(mm)
    
                if sec2[11] == 1:  # OPTIONS
                    if "[" in s1:
                        continue
                    # mm = s1.split()
                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
                            optionsSection.append(mm)
    
                if sec2[12] == 1:  # LABELS
                    if "[" in s1:
                        continue
                    # mm = s1.split()
                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
                            labelsSection.append(mm)

                if section_name == Tag.section_name:
                    if '[' in s1:
                        continue

                    if len(mm) > 1:
                        if mm[0][0] == ';':
                            pass
                        else:
                            tag = Tag(mm[0], mm[1], mm[2])
                            self.tags.append(tag)
                    
    
    def read_line(self, s1):
        # Strip new line
        s1 = s1.strip('\r\n')
    
        # Strip stuff beyond ;
        pos = s1.rfind(';')
        description = ''
        if pos > 0:
            # Get description
            description = s1[pos + 1:-1]
    
            # Strip description
            s1 = s1[:pos]
    
        mm = re.split('[\t\s]+', s1.strip('\t ;'))
    
        return mm, description
    
    ## Node Coordinates
    def getBinNodeCoordinates(self):
        return self.mm[40], self.mm[41], self.mm[42], self.mm[43]  # ,mm[44],mm[45],mm[46],mm[47]
        # x,y,x1,y1,x2,y2,vertx,verty] #40#41#42#43#44#45#46#47
    
    
    EN_ELEVATION = 0  # /* Node parameters */
    EN_BASEDEMAND = 1
    EN_PATTERN = 2
    EN_EMITTER = 3
    EN_INITQUAL = 4
    EN_SOURCEQUAL = 5
    EN_SOURCEPAT = 6
    EN_SOURCETYPE = 7
    EN_TANKLEVEL = 8
    EN_DEMAND = 9
    EN_HEAD = 10
    EN_PRESSURE = 11
    EN_QUALITY = 12
    EN_SOURCEMASS = 13
    EN_INITVOLUME = 14
    EN_MIXMODEL = 15
    EN_MIXZONEVOL = 16
    
    EN_TANKDIAM = 17
    EN_MINVOLUME = 18
    EN_VOLCURVE = 19
    EN_MINLEVEL = 20
    EN_MAXLEVEL = 21
    EN_MIXFRACTION = 22
    EN_TANK_KBULK = 23
    
    EN_DIAMETER = 0  # /* Link parameters */
    EN_LENGTH = 1
    EN_ROUGHNESS = 2
    EN_MINORLOSS = 3
    EN_INITSTATUS = 4
    EN_INITSETTING = 5
    EN_KBULK = 6
    EN_KWALL = 7
    EN_FLOW = 8
    EN_VELOCITY = 9
    EN_HEADLOSS = 10
    EN_STATUS = 11
    EN_SETTING = 12
    EN_ENERGY = 13
    
    EN_DURATION = 0  # /* Time parameters */
    EN_HYDSTEP = 1
    EN_QUALSTEP = 2
    EN_PATTERNSTEP = 3
    EN_PATTERNSTART = 4
    EN_REPORTSTEP = 5
    EN_REPORTSTART = 6
    EN_RULESTEP = 7
    EN_STATISTIC = 8
    EN_PERIODS = 9
    
    EN_NODECOUNT = 0  # /* Component counts */
    EN_TANKCOUNT = 1
    EN_LINKCOUNT = 2
    EN_PATCOUNT = 3
    EN_CURVECOUNT = 4
    EN_CONTROLCOUNT = 5
    
    EN_JUNCTION = 0  # /* Node types */
    EN_RESERVOIR = 1
    EN_TANK = 2
    
    EN_CVPIPE = 0  # /* Link types */
    EN_PIPE = 1
    EN_PUMP = 2
    EN_PRV = 3
    EN_PSV = 4
    EN_PBV = 5
    EN_FCV = 6
    EN_TCV = 7
    EN_GPV = 8
    
    EN_NONE = 0  # /* Quality analysis types */
    EN_CHEM = 1
    EN_AGE = 2
    EN_TRACE = 3
    
    EN_CONCEN = 0  # /* Source quality types */
    EN_MASS = 1
    EN_SETPOINT = 2
    EN_FLOWPACED = 3
    
    EN_CFS = 0  # /* Flow units types */
    EN_GPM = 1
    EN_MGD = 2
    EN_IMGD = 3
    EN_AFD = 4
    EN_LPS = 5
    EN_LPM = 6
    EN_MLD = 7
    EN_CMH = 8
    EN_CMD = 9
    
    EN_TRIALS = 0  # /* Misc. options */
    EN_ACCURACY = 1
    EN_TOLERANCE = 2
    EN_EMITEXPON = 3
    EN_DEMANDMULT = 4
    
    EN_LOWLEVEL = 0  # /* Control types */
    EN_HILEVEL = 1
    EN_TIMER = 2
    EN_TIMEOFDAY = 3
    
    EN_AVERAGE = 1  # /* Time statistic types.    */
    EN_MINIMUM = 2
    EN_MAXIMUM = 3
    EN_RANGE = 4
    
    EN_MIX1 = 0  # /* Tank mixing models */
    EN_MIX2 = 1
    EN_FIFO = 2
    EN_LIFO = 3
    
    EN_NOSAVE = 0  # /* Save-results-to-file flag */
    EN_SAVE = 1
    EN_INITFLOW = 10  # /* Re-initialize flow flag   */
    
    Open = 1
    Closed = 0
    
    # Constants for units
    FlowUnits = {EN_CFS: "cfs",
                 EN_GPM: "gpm",
                 EN_MGD: "a-f/d",
                 EN_IMGD: "mgd",
                 EN_AFD: "Imgd",
                 EN_LPS: "L/s",
                 EN_LPM: "Lpm",
                 EN_MLD: "m3/h",
                 EN_CMH: "m3/d",
                 EN_CMD: "ML/d"}
    
    # Constants for links
    TYPELINK = {EN_CVPIPE: "CV",
                EN_PIPE: "PIPE",
                EN_PUMP: "PUMP",
                EN_PRV: "PRV",
                EN_PSV: "PSV",
                EN_PBV: "PBV",
                EN_FCV: "FCV",
                EN_TCV: "TCV",
                EN_GPV: "GPV"}
    
    # Constants for nodes
    TYPENODE = {EN_JUNCTION: "JUNCTION",
                EN_RESERVOIR: "RESERVOIR",
                EN_TANK: "TANK"}
    
    # Constants for controls
    TYPECONTROL = {EN_LOWLEVEL: "LOWLEVEL",
                   EN_HILEVEL: "HIGHLEVEL",
                   EN_TIMER: "TIMER",
                   EN_TIMEOFDAY: "TIMEOFDAY"}
    
    # Constants for mixing models
    TYPEMIXMODEL = {EN_MIX1: "MIX1",
                    EN_MIX2: "MIX2",
                    EN_FIFO: "FIFO",
                    EN_LIFO: "LIFO"}
    
    # Constants for quality
    TYPEQUALITY = {EN_NONE: "NONE",
                   EN_CHEM: "CHEM",
                   EN_AGE: "AGE",
                   EN_TRACE: "TRACE"}
    
    # Constants for sources
    TYPESOURCE = {EN_CONCEN: "CONCEN",
                  EN_MASS: "MASS",
                  EN_SETPOINT: "SETPOINT",
                  EN_FLOWPACED: "FLOWPACED"}
    
    # Constants for statistics
    TYPESTATS = {EN_NONE: "NONE",
                 EN_AVERAGE: "AVERAGE",
                 EN_MINIMUM: "MINIMUM",
                 EN_MAXIMUM: "MAXIMUM",
                 EN_RANGE: "RANGE"}
