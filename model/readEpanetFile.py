# From https://plugins.qgis.org/plugins/ImportEpanetInpFiles/

from builtins import range
import re

def LoadFile(inp):
    global inpname, mm
    mm = []
    # getPathPlugin = os.path.dirname(os.path.realpath(__file__))+"\\"
    # inpname = getPathPlugin + inp
    inpname = inp


def BinUpdateClass():
    global mm
    mm = getBinInfo()
    return mm


## get Info
def getBinNodeReservoirIndex():
    ind = list(range(getBinNodeJunctionCount() + 1, getBinNodeJunctionCount() + getBinNodeReservoirCount() + 1))
    return ind


def getBinNodeTankIndex():
    ind = list(range(getBinNodeJunctionCount() + getBinNodeReservoirCount() + 1, getBinNodeCount() + 1))
    return ind


def getBinNodeDemandPatternID():
    global mm
    return mm[3]


def getBinNodeJunctionCount():
    global mm
    return mm[4]


def getBinNodeReservoirCount():
    global mm
    return mm[7]


def getBinNodeIndex(id):
    nodeNameID = getBinNodeNameID()
    return nodeNameID.index(id)


def getBinNodeNameID():
    global mm
    return mm[0] + mm[5] + mm[8]


def getBinNodeJunctionNameID():
    global mm
    return mm[0]


def getBinReservoirNameID():
    global mm
    return mm[5]


# def getBinNodeElevations():
#     global mm
#     nodeElevations=getBinNodeJunctionElevations()
#     for i in range(len(mm[6])):
#         nodeElevations.append(mm[6][i])#reservoirs
#     for i in range(len(mm[6])):
#         nodeElevations.append(mm[9][i])
#     return nodeElevations

def getBinNodeJunctionElevations():
    global mm
    return mm[1]


def getBinNodeReservoirElevations():
    global mm
    return mm[6]


def getBinNodeBaseDemands():
    global mm
    return mm[2]


# Tanks Info
def getBinNodeTankNameID():
    global mm
    return mm[8]


def getBinNodeTankCount():
    return len(getBinNodeTankNameID())


def getBinNodeTankElevations():
    global mm
    return mm[9]


def getBinNodeTankInitialLevel():
    global mm
    return mm[10]


def getBinNodeTankMinimumWaterLevel():
    global mm
    return mm[11]


def getBinNodeTankMaximumWaterLevel():
    global mm
    return mm[12]


def getBinNodeTankDiameter():
    global mm
    return mm[13]


def getBinNodeTankMinimumWaterVolume():
    global mm
    return mm[14]


def getBinNodeTankVolumeCurveID():
    global mm
    return mm[35]


# Get Links Info
def getBinLinkPumpIndex():
    ind = []
    for i in range(getBinLinkPipeCount() + 1, getBinLinkPipeCount() + getBinLinkPumpCount() + 1):
        ind.append(i - 1)
    return ind


def getBinLinkValveIndex():
    ind = []
    for i in range(getBinLinkPipeCount() + getBinLinkPumpCount() + 1, getBinLinkCount() + 1):
        ind.append(i - 1)
    return ind


def getBinLinkIndex(id):
    linkNameID = getBinLinkNameID()
    return linkNameID.index(id)


def getBinLinkNameID():
    global mm
    return mm[15] + mm[22] + mm[27]


def getBinLinkLength():
    ll = getBinLinkPipeLengths()
    for i in range(getBinLinkPipeCount() + 1, getBinLinkCount() + 1):
        ll.append(0)
    return ll


def getBinLinkDiameter():
    ll = getBinLinkPipeDiameters()
    vld = getBinLinkValveDiameters()
    for i in range(getBinLinkPipeCount() + 1, getBinLinkPipeCount() + getBinLinkPumpCount() + 1):
        ll.append(0)
    for i in range(getBinLinkValveCount()):
        ll.append(vld[i])
    return ll


def getBinLinkRoughnessCoeff():
    ll = getBinLinkPipeRoughness()
    for i in range(getBinLinkPipeCount() + 1, getBinLinkCount() + 1):
        ll.append(0)
    return ll


def getBinLinkMinorLossCoeff():
    ll = getBinLinkPipeMinorLoss()
    vld = getBinLinkValveMinorLoss()
    for i in range(getBinLinkPipeCount() + 1, getBinLinkPipeCount() + getBinLinkPumpCount() + 1):
        ll.append(0)
    for i in range(getBinLinkValveCount()):
        ll.append(vld[i])
    return ll


def getBinLinkPipeCount():
    return len(getBinLinkPipeNameID())


def getBinLinkPipeNameID():
    global mm
    return mm[15]


def getBinLinkFromNode():
    global mm
    return mm[16]


def getBinLinkToNode():
    global mm
    return mm[17]


def getBinLinkPipeLengths():
    global mm
    return mm[18]


def getBinLinkPipeDiameters():
    global mm
    return mm[19]


def getBinLinkPipeRoughness():
    global mm
    return mm[20]


def getBinLinkPipeMinorLoss():
    global mm
    return mm[21]


# Get Pumps Info
def getBinLinkPumpCount():
    return len(getBinLinkPumpNameID())


def getBinLinkPumpNameID():
    global mm
    return mm[22]


def getBinLinkPumpPatterns():
    global mm
    return mm[23]


def getBinLinkPumpCurveNameID():
    global mm
    return mm[24]


def getBinLinkPumpPower():
    global mm
    return mm[25]


def getBinLinkPumpNameIDPower():
    global mm
    return mm[26]


def getBinLinkPumpSpeed():
    global mm
    return mm[38]


def getBinLinkPumpPatternsPumpID():
    global mm
    return mm[39]

def getBinLinkPumpSpeedID():
    return mm[62]

# Get Valves Info
def getBinLinkValveCount():
    return len(getBinLinkValveNameID())


def getBinLinkValveNameID():
    global mm
    return mm[27]


def getBinLinkValveDiameters():
    global mm
    return mm[28]


def getBinLinkValveType():
    global mm
    return mm[29]


def getBinLinkValveSetting():
    global mm
    return mm[30]


def getBinLinkValveMinorLoss():
    global mm
    return mm[31]


def getBinNodesConnectingLinksID():
    return [mm[16], mm[17]]


def getBinNodesConnectingLinksIndex():
    NodesConnectingLinksID = getBinNodesConnectingLinksID()
    nodeInd = []
    for i in range(getBinLinkCount()):
        nodeInd.append([getBinNodeIndex(NodesConnectingLinksID[0][i]), getBinNodeIndex(NodesConnectingLinksID[1][i])])
    return nodeInd


def getBinLinkCount():
    return getBinLinkPipeCount() + getBinLinkPumpCount() + getBinLinkValveCount()


def getBinNodeCount():
    return getBinNodeJunctionCount() + getBinNodeReservoirCount() + getBinNodeTankCount()


# Status
def getBinLinkInitialStatus():
    global mm
    return mm[32]


def getBinLinkInitialStatusNameID():
    global mm
    return mm[33]


# Curves
def getBinCurvesNameID():
    global mm
    return mm[36]


def getBinCurvesXY():
    global mm
    return mm[37]


def getBinCurveCount():
    global mm
    return len(set(mm[36]))


def getDemandsSection():
    global mm
    return mm[44]


def getStatusSection():
    global mm
    return mm[45]


def getEmittersSection():
    global mm
    return mm[46]


def getControlsSection():
    global mm
    return mm[47]


def getPatternsSection():
    global mm
    return mm[48]


def getCurvesSection():
    global mm
    return mm[49], mm[50]


def getQualitySection():
    global mm
    return mm[51]


def getRulesSection():
    global mm
    return mm[52]


def getSourcesSection():
    global mm
    return mm[53]


def getEnergySection():
    global mm
    return mm[54]


def getReactionsSection():
    global mm
    return mm[55]


def getReactionsOptionsSection():
    global mm
    return mm[56]


def getMixingSection():
    global mm
    return mm[57]


def getTimesSection():
    global mm
    return mm[58]


def getOptionsSection():
    global mm
    return mm[59]


def getReportSection():
    global mm
    return mm[60]


def getLabelsSection():
    global mm
    return mm[61]


# Descriptions
def get_junctions_desc():
    global mm
    return mm[63]


def get_reservoirs_desc():
    global mm
    return mm[64]


def get_tanks_desc():
    global mm
    return mm[65]


def get_nodes_desc():
    global mm
    return mm[63] + mm[64] + mm[65]


def get_pipes_desc():
    global mm
    return mm[66]


def get_pumps_desc():
    global mm
    return mm[67]


def get_valves_desc():
    global mm
    return mm[68]


def get_links_desc():
    global mm
    return mm[66] + mm[67] + mm[68]


# Get all info
def getBinInfo():
    global inpname
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



    with open(inpname) as openfileobject:
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
                        tags # 69
                        ]

            elif "[JUNCTIONS]" in s1:
                sec[0] = 1
                continue
            elif "[RESERVOIRS]" in s1:
                sec = [0] * num
                sec[1] = 1
                continue
            elif "[TANKS]" in s1:
                sec = [0] * num
                sec[2] = 1
                continue
            elif "[PIPES]" in s1:
                sec = [0] * num
                sec[3] = 1
                continue
            elif "[PUMPS]" in s1:
                sec = [0] * num
                sec[4] = 1
                continue
            elif "[VALVES]" in s1:
                sec = [0] * num
                sec[5] = 1
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
                continue
            elif "[DEMANDS]" in s1:
                sec = [0] * num
                sec[8] = 1
                continue
            elif (
                "[JUNCTIONS]" in s1 or "[RESERVOIRS]" in s1 or "[TANKS]" in s1 or "[PIPES]" in s1 or "[PUMPS]" in s1 or "[VALVES]" in s1):
                ok = 1
            elif "[TAGS]" in s1 and ok == 0:
                sec = [0] * num
                continue
            elif "[PATTERNS]" in s1:
                sec = [0] * num
                sec[6] = 1
                continue
            elif "[CURVES]" in s1:
                sec = [0] * num
                sec[9] = 1
                continue
            elif "[CONTROLS]" in s1:
                sec = [0] * num
                sec[10] = 1
                continue
            elif "[COORDINATES]" in s1:
                sec2 = [0] * num
                sec2[0] = 1
                continue

            elif "[VERTICES]" in s1:
                sec2 = [0] * num
                sec2[1] = 1
                continue
            elif "[LABELS]" in s1:
                sec2 = [0] * num
                sec2[12] = 1
                continue
            elif "[EMITTERS]" in s1:
                sec2 = [0] * num
                sec2[2] = 1
                continue
            elif "[RULES]" in s1:
                sec = [0] * num
                sec2 = [0] * num
                sec2[3] = 1
                continue
            elif "[ENERGY]" in s1:
                sec2 = [0] * num
                sec2[6] = 1
                if rules != []:
                    rulesSection.append(rules)
                continue
            elif "[QUALITY]" in s1:
                sec2 = [0] * num
                sec = [0] * num
                sec2[4] = 1
                continue
            elif "[SOURCES]" in s1:
                sec2 = [0] * num
                sec2[5] = 1
                continue
            elif "[REACTIONS]" in s1:
                sec2 = [0] * num
                sec2[7] = 1
                continue
            elif "[MIXING]" in s1:
                sec2 = [0] * num
                sec2[8] = 1
                continue
            elif "[TIMES]" in s1:
                sec2 = [0] * num
                sec2[9] = 1
                continue
            elif "[REPORT]" in s1:
                sec2 = [0] * num
                sec2[10] = 1
                continue
            elif "[OPTIONS]" in s1:
                sec2 = [0] * num
                sec2[11] = 1
                continue
            elif "[BACKDROP]" in s1:
                sec2 = [0] * num
                continue
            elif "[" in s1:
                continue

            if s1.strip('\t ').startswith(';'):
                continue
            mm, desc = read_mm(s1)

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


def read_mm(s1):
    # Strip new line
    s1 = s1.strip('\r\n')

    # Strip stuff beyond ;
    pos = s1.rfind(';')
    description = ''
    if pos > 0:
        # Get description
        description = s1[pos + 1:]

        # Strip description
        s1 = s1[:pos]

    mm = re.split('[\t\s]+', s1.strip('\t ;'))

    return mm, description

## Node Coordinates
def getBinNodeCoordinates():
    global mm
    return mm[40], mm[41], mm[42], mm[43]  # ,mm[44],mm[45],mm[46],mm[47]
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