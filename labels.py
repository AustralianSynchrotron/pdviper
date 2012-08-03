# -*- coding: utf-8 -*-

def get_value_scale_label(scale):
    labels = { 'log': u'log₁₀N', 'linear': 'N', 'sqrt': u'√N' }
    return labels[scale]

