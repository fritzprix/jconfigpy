import json
from os import path
import os
from ErrorType import FileNotExistError
from Item import JConfigEnum
from Item import JConfigBool
from Item import JConfigHex
from Item import JConfigInt
from Item import JConfigString
from Item import JConfigTristate

from Recipe import JConfigRecipe
from Recipe import JConfigRepo
from VariableMonitor import Monitor


class JConfig:

    def on_update_var(self, var, updated_val):
        if var in self._var_map:
            self._var_map.update({var: updated_val})
        if var in self._depend:
            self._visibility = self._var_pub.check_depend(**self._depend)
        if var in self._unresolved_path:
            self._unresolved_path.update({var: updated_val})

    def set_config(self, config_file):
        if not path.exists(config_file):
            raise FileNotExistError(config_file)
        self._jconfig_file = config_file
        self._base_dir = path.split(config_file)[0]

    def get_childs(self):
        return self._child

    def get_items(self):
        return self._items

    def write_recipe(self, fp, fmt="include {0}\n"):
        if not isinstance(fp, file):
            return
        for recipe in self._recipes:
            fp.write(fmt.format(recipe.get_resolved_path()))
        for child in self._child:
            child.write_recipe(fp, fmt)

    def write_genlist(self, fp, fmt="#define {0} {1}\n"):
        if not isinstance(fp, file):
            return
        for item in self._items:
            gen = item.get_resolved_genlist()
            if len(gen) > 0:
                for gi in gen:
                    fp.write(fmt.format(gi, gen[gi]))

        for child in self._child:
            child.write_genlist(fp, fmt)

    def is_visible(self):
        return self._visibility

    def parse(self):
        if len(self._unresolved_path) > 0:
            # resolve path before opening the file
            for pv in self._unresolved_path:
                path_var = '$' + pv
                self._jconfig_file = self._jconfig_file.replace(path_var, self._unresolved_path[pv])
        if not path.exists(self._jconfig_file):
            raise FileNotExistError(self._jconfig_file)
        with open(self._jconfig_file, 'r') as fp:
            config_json = json.load(fp, encoding='utf-8')
            for key in config_json:
                config_type = config_json[key]['type']
                if 'enum' in config_type:
                    self._items.append(JConfigEnum(key, self._var_pub, **config_json[key]))
                elif 'bool' in config_type:
                    self._items.append(JConfigBool(key, self._var_pub, **config_json[key]))
                elif 'int' in config_type:
                    self._items.append(JConfigInt(key, self._var_pub, **config_json[key]))
                elif 'hex' in config_type:
                    self._items.append(JConfigHex(key, self._var_pub, **config_json[key]))
                elif 'string' in config_type:
                    self._items.append(JConfigString(key, self._var_pub, **config_json[key]))
                elif 'tristate' in config_type:
                    self._items.append(JConfigTristate(key, self._var_pub, **config_json[key]))
                elif 'config' in config_type:
                    config_path = config_json[key]['path']
                    config_path = path.abspath(path.join(self._base_dir, config_path))
                    self._child.append(JConfig(name=key,
                                               jconfig_file=config_path,
                                               root_dir=self._root,
                                               **config_json[key]))
                elif 'recipe' in config_type:
                    self._recipes.append(JConfigRecipe(key,
                                                       self._var_pub,
                                                       self._base_dir,
                                                       self._var_map,
                                                       **config_json[key]))
                elif 'repo' in config_type:
                    repositoy = JConfigRepo(var_pub=self._var_pub,
                                            base_dir=self._base_dir,
                                            root_dir=self._root,
                                            var_map=self._var_map,
                                            **config_json[key])
                    print self._base_dir
                    print self._root
                    repositoy.resolve_repo()
                    self._repos.append(repositoy)

    def __str__(self):
        report_str = str('>>> Config : {}\n'.format(self._name))
        for item in self._items:
            report_str += str(item)
        report_str += '<<< Config : {}\n'.format(self._name)
        return report_str

    def __init__(self, name='root', jconfig_file='./config.json', root_dir=None, var_map=None, parent=None, **kwargs):
        self._name = name
        self._root = root_dir
        self._jconfig_file = jconfig_file
        self._parent = parent
        self._var_map = dict(iterable=var_map)
        self._unresolved_path = {}
        self._items = []
        self._child = []
        self._recipes = []
        self._repos = []
        self._visibility = True

        try:
            self._var_pub = Monitor()
        except Monitor as var_pub:
            self._var_pub = var_pub

        self._depend = kwargs.get('depend', {})
        self._name = name
        self._var_pub.get_update(self._var_map)
        self._base_dir = path.abspath(path.abspath(path.dirname(jconfig_file)))
        self._jconfig_file = path.abspath(jconfig_file)
        autogen_file = path.abspath(path.join(self._base_dir, './autorecipe.mk'))
        print autogen_file
        if path.exists(autogen_file):
            os.remove(autogen_file)

        if '$' in self._jconfig_file:
            '''
            unresolved part exists in config file path
            '''
            config_path, p = path.split(self._jconfig_file)
            while p != '':
                if '$' in p:
                    path_var = p.split('$')[1]
                    if path_var in self._var_map:
                        self._unresolved_path.update({path_var: self._var_map[path_var]})
                    else:
                        self._unresolved_path.update({path_var: ''})
                    self._var_pub.subscribe_variable_change(path_var, self)
                config_path, p = path.split(config_path)

        if len(self._depend) > 0:
            self._visibility = self._var_pub.check_depend(**self._depend)
            for key in self._depend:
                self._var_pub.subscribe_variable_change(key, self)

    def __del__(self):
        if len(self._unresolved_path) > 0:
            for upath in enumerate(self._unresolved_path):
                self._var_pub.unsubscribe_variable_change(upath, self)

        if len(self._var_map) > 0:
            for var in enumerate(self._var_map):
                self._var_pub.unsubscribe_variable_change(var, self)

    _DEFAULT_FILE = './config.json'

