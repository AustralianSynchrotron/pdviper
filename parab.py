import re
from os import walk
from os.path import abspath, join


def load_params(filename):
    data = open(filename).readlines()

    if not data:
        return {}

    collection_date = data[0]
    data = data[1:]

    regex = re.compile(r'(.*) = (.*)')
    param_regex = re.compile(r'[\w:.]+ (.*) (.*)')

    params = {}
    for line in data:
        m = regex.match(line)
        if m:
            k, v = m.group(1, 2)
            params[k] = v
            continue

        m = param_regex.match(line)
        if m:
            k, v = m.group(2, 1)
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    pass
            k = k.replace('_', ' ')
            params[k] = v
            continue
    params['date'] = collection_date
    return params


def get_filelist(base_dir):
    files = []
    for dirpath, dirnames, filenames in walk(base_dir):
        wanted_files = [ fn for fn in filenames if fn.endswith('.parab') ]
        wanted_files = [ abspath(join(dirpath, fn)) for fn in wanted_files ]
        files.extend(wanted_files)
    return files

def load_all_params():
    files = get_filelist('.')
    params_per_file = [ load_params(fn) for fn in files ]
    print params_per_file

    for p in params_per_file:
        print p

    keys = set()
    for params in params_per_file:
        keys = keys.union(set(params.keys()))

    params_list = []
    for key in keys:
        for params in params_per_file:
            params.get(key, None)

