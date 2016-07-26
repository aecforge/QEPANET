class Curve:
    section_name = 'CURVES'

    def __init__(self, name, id):
        self.id = id
        self.name = name
        self.xs = []
        self.ys = []

    def add_xy(self, x, y):
        self.xs.append(x)
        self.ys.append(y)


class Pattern:
    section_name = 'PATTERNS'

    def __init__(self, name, id):
        self.id = id
        self.name = name
        self.values = []

    def add_value(self, val):
        self.values.append(val)


class Energy:
    section_name = 'ENERGY'

    def __init__(self):
        pass


class Status:
    section_name = 'STATUS'

    def __init__(self):
        pass


class Controls:
    section_name = 'CONTROLS'

    def __init__(self):
        pass


class Rules:
    section_name = 'RULES'

    def __init__(self):
        pass


class Demand:
    section_name = 'DEMANDS'

    def __init__(self):
        pass