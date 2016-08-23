class Options:

    section_name = 'OPTIONS'

    unit_sys_si = 'SI'
    unit_sys_us = 'US'
    units_sys = [unit_sys_si, unit_sys_us]
    units_sys_text = {unit_sys_si: 'SI METRIC',
                      unit_sys_us: 'US CUSTOMARY'}

    units_diameter_pipes = {unit_sys_si: 'mm',
                            unit_sys_us: 'in'}

    units_diameter_tanks = {unit_sys_si: 'm',
                            unit_sys_us: 'ft'}

    units_flow = {unit_sys_si:
                      ['LPS', 'LPM', 'MLD', 'CMH', 'CMD'],
                  unit_sys_us:
                      ['CFS', 'GPM', 'MGD', 'IMGD', 'AFD']}

    units_flow_text = {unit_sys_si:
                           ['LPS - liters per second',
                            'LPM - liters per minute',
                            'MLD - million liters per day',
                            'CMH - cubic meters per hour',
                            'CMD - cubic meters per day'],
                       unit_sys_us:
                           ['CFS - cubic feet per second',
                            'GPM - gallons per minute',
                            'MGD - million gallons per day',
                            'IMGD - Imperial MGD',
                            'AFD - acre-feet per day']}  # TODO: sofcode

    units_depth = {unit_sys_si: 'm',
                   unit_sys_us: 'ft'}

    units_volume = {unit_sys_si: 'm3',
                    unit_sys_us: 'cb.ft'}

    headloss_hw = 'H-W'
    headloss_dw = 'D-W'
    headloss_cm = 'C-M'
    headlosses_text = {headloss_hw: 'Hazen-Williams',
                       headloss_dw: 'Darcy-Weisbach',
                       headloss_cm: 'Chezy-Manning'}

    units_power = {unit_sys_si: 'kW',
                   unit_sys_us: 'hp'}

    units_pressure = {unit_sys_si: 'm',
                      unit_sys_us: 'psi'}

    units_roughness = {unit_sys_si:
                           {headloss_hw: '-',
                            headloss_dw: 'mm',
                            headloss_cm: '-'},
                       unit_sys_us:
                           {headloss_hw: '-',
                            headloss_dw: '10-3 ft',
                            headloss_cm: '-'}
                       }

    def __init__(self):
            self.units = Options.unit_sys_si
            self.flow_units = Options.units_flow[self.units][0]
            self.headloss = Options.headloss_cm
            self.hydraulics = Hydraulics()
            self.quality = Quality()
            self.viscosity = 1
            self.diffusivity = 1
            self.spec_gravity = 1
            self.trials = 40
            self.accuracy = 0.001
            self.unbalanced = Unbalanced()
            self.pattern = 1
            self.demand_mult = 1
            self.emitter_exp = 0.5
            self.tolerance = 0.01


class Hydraulics:

    action_use = 0
    action_save = 1

    def __init__(self):
        self.use_hydraulics = False
        self.action = None
        self.file = None


class Quality:

    quality_none = 0
    quality_chemical = 1
    quality_age = 2
    quality_trace = 3

    quality_text = {quality_none: 'None',
                    quality_chemical: 'Chemical',
                    quality_age: 'Age',
                    quality_trace: 'Trace'}

    quality_units_mgl = 'mgL'
    quality_units_ugl = 'ugL'

    quality_units_text = {quality_units_mgl: 'mg/L',
                          quality_units_ugl: 'ug/L'}

    def __init__(self):
        self.parameter = Quality.quality_none
        self.mass_units = Quality.quality_units_mgl
        self.relative_diff = 1
        self.trace_junction_id = None
        self.quality_tol = 0.01


class Unbalanced:
    unb_stop = 0
    unb_continue = 1

    unb_text = {unb_stop: 'Stop',
                unb_continue: 'Contunue'}

    def __init__(self):
        self.unbalanced = Unbalanced.unb_stop
        self.trials = 0
