class Curve:
    section_name = 'CURVES'

    def __init__(self, id, desc=None):
        self.id = id
        self.desc = desc
        self.xs = []
        self.ys = []

    def append_xy(self, x, y):
        self.xs.append(x)
        self.ys.append(y)


class Controls:
    section_name = 'CONTROLS'

    def __init__(self):
        pass


class Demand:
    section_name = 'DEMANDS'

    def __init__(self):
        pass


class Energy:

    section_name = 'ENERGY'

    def __init__(self):
        self.pump_efficiency = 75
        self.energy_price = 0
        self.price_pattern = None
        self.demand_charge = 0


class Pattern:
    section_name = 'PATTERNS'
    section_header = 'ID              	Multipliers'

    def __init__(self, id, desc=None, values=None):
        self.id = id
        self.desc = desc
        if values is None:
            self.values = []
        else:
            self.values = values[:]

    def add_value(self, val):
        self.values.append(val)


class Rule:
    section_name = 'RULES'

    def __init__(self):
        pass


class Status:
    section_name = 'STATUS'
    section_header = 'ID              	Status/Setting'

    def __init__(self):
        pass