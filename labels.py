# -*- coding: utf-8 -*-

def get_value_scale_label(scale, mpl=False):
    labels =     { 'log':u'log10N',       'linear':'N', 'sqrt':u'√N' }
    mpl_labels = { 'log':r'log${}_{10}$N', 'linear':'N', 'sqrt':r"$\sqrt{N}$" }
    if mpl:
        return mpl_labels[scale]
    else:
        return labels[scale]

