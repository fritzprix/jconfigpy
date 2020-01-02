from os import path


class Monitor:

    _SINGLE_OBJECT = None
    _FILE_WRITE_FORMAT = 'CONFIG_{var}={val}\n'

    def __init__(self):
        if Monitor._SINGLE_OBJECT is not None:
            raise Monitor._SINGLE_OBJECT
        self._var_map = {}
        self._sub_map = {}
        Monitor._SINGLE_OBJECT = self

    def notify_variable_change(self, var, update_val):
        if var not in self._var_map:
            self._var_map.update({var: update_val})
        else:
            self._var_map[var] = update_val
        if var in self._sub_map:
            for subsc in self._sub_map[var]:
                subsc.on_update_var(var, update_val)

    def lookup_variable(self, var):
        if var not in self._var_map:
            return None
        return self._var_map[var]

    def check_depend(self, **kwargs):
        for key, val in kwargs.iteritems():
            cval = self._var_map.get(key, None)
            if cval is None or cval != val:
                return False
        return True

    def subscribe_variable_change(self, var, config_item):
        try:
            sub_list = self._sub_map[var]
        except KeyError:
            self._sub_map.update({var: []})
            sub_list = self._sub_map[var]
        sub_list.append(config_item)

    def unsubscribe_variable_change(self, var, config_item):
        if var not in self._sub_map:
            return
        self._sub_map[var].remove(config_item)

    def resolve_path(self, pth):
        if '$' not in pth:
            return pth
        head, tail = path.split(pth)
        while tail != '':
            if '$' in tail:
                key = tail.split('$')[-1]
                if key in self._var_map:
                    pth = pth.replace(tail, self._var_map[key])
            head, tail = path.split(head)
        return pth

    def get_update(self, var_map):
        if not isinstance(var_map, dict):
            return
        var_map.update(self._var_map)

    def write(self, fp, key=None):
        if not isinstance(fp, file):
            raise TypeError('fp is not instance of file')
        if key is not None and key in self._var_map:
            fp.write(Monitor._FILE_WRITE_FORMAT.format(var=key, val=self._var_map[key]))
            return
        for key in self._var_map:
            fp.write(Monitor._FILE_WRITE_FORMAT.format(var=key, val=self._var_map[key]))
