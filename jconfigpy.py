import sys
import json
import re
from os import path
from os import environ


class FileNotExistError(BaseException):
    def __init__(self, msg):
        self.message = msg
        BaseException.__init__(self)

    def __str__(self):
        return self.message


class ConfigVariableMonitor:

    _SINGLE_OBJECT = None
    _FILE_WRITE_FORMAT = 'CONFIG_{var}={val}\n'

    def __init__(self):
        if ConfigVariableMonitor._SINGLE_OBJECT is not None:
            raise ConfigVariableMonitor._SINGLE_OBJECT
        self._var_map = {}
        self._sub_map = {}
        ConfigVariableMonitor._SINGLE_OBJECT = self

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
            if cval is None or cval is not val:
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
        npth = str(pth)
        for p in pth.split('/'):
            if '$' in p:
                key = p.split('$')[-1]
                if key in self._var_map:
                    npth = npth.replace(p, self._var_map[key])
        return npth

    def get_update(self, var_map):
        if not isinstance(var_map, dict):
            return
        var_map.update(self._var_map)

    def write(self, fp, key=None):
        if not isinstance(fp, file):
            raise TypeError('fp is not instance of file')
        if key is not None and key in self._var_map:
            fp.write(ConfigVariableMonitor._FILE_WRITE_FORMAT.format(var=key, val=self._var_map[key]))
            return
        for key in self._var_map:
            fp.write(ConfigVariableMonitor._FILE_WRITE_FORMAT.format(var=key, val=self._var_map[key]))


class JConfigItem:
    _NIE_MESSAGE = '{} is not implemented'
    _REPORT_FORMAT = 'name : {name} \n' \
                     'default value : {dval}\n' \
                     'user value : {uval}\n' \
                     'depends on : {deplist}\n' \
                     'is_visible : {visible}\n'

    def get_prompt(self):
        raise NotImplementedError(JConfigItem._NIE_MESSAGE.format(JConfigItem.get_prompt))

    def get_help(self):
        raise NotImplementedError(JConfigItem._NIE_MESSAGE.format(JConfigItem.get_help))

    def get_user_value(self):
        if self._user_val is None:
            if self._def_val is None:
                return None
            else:
                return self._def_val
        return self._user_val

    def get_default_value(self):
        return self._def_val

    def get_name(self):
        return self._name

    def set_user_value(self, val):
        if self._user_val != val:
            self._var_pub.notify_variable_change(self._name, val)
        self._user_val = val

    def on_update_var(self, var, update_val):
        if var in self._depend:
            self._depend.update({var: update_val})
            self._visiblility = self._var_pub.check_depend(**self._depend)
            return True
        return False

    def get_type(self):
        return self._type

    def is_visible(self):
        return self._visiblility

    def __init__(self, name, type_, var_pub, **kwargs):
        self._user_val = None
        self._def_val = kwargs.get('default', '')
        self._var_pub = None
        self._name = name
        self._visiblility = True
        self._depend = kwargs.get('depend', {})
        self._type = type_

        if not isinstance(var_pub, ConfigVariableMonitor):
            raise TypeError(_TYPE_ERROR_FORMAT.format('var_pub', ConfigVariableMonitor))
        self._var_pub = var_pub

        if len(self._depend) > 0:
            self._visiblility = var_pub.check_depend(**self._depend)
            for var in enumerate(self._depend):
                self._var_pub.subscribe_variable_change(var, self)  # subscribe variable change

    def __str__(self):

        return JConfigItem._REPORT_FORMAT.format(name=self._name,
                                                 dval=self._def_val,
                                                 uval=self._user_val,
                                                 deplist=self._depend,
                                                 visible=self._visiblility)

    def __del__(self):
        if self._var_pub is None:
            return
        for var in enumerate(self._depend):
            self._var_pub.unsubscribe_variable_change(var, self)


class JConfigString(JConfigItem):

    _DEFAULT_PROMPT = 'Enter {0} (string) '
    _DEFAULT_HELP = [
        'No Help Message'
    ]

    def get_help(self):
        return self._help

    def get_prompt(self):
        return self._prompt

    def set_user_value(self, val):
        if len(val) == 0:
            raise ValueError('string type should not be empty ')
        JConfigItem.set_user_value(self, val)

    def __init__(self, name, var_pub, **kwargs):

        self._prompt = ""
        self._help = []
        self._import = False

        JConfigItem.__init__(self, name, 'string', var_pub, **kwargs)

        self._prompt = kwargs.get('prompt', JConfigString._DEFAULT_PROMPT.format(self._name))
        self._help = kwargs.get('help', JConfigString._DEFAULT_HELP)
        self._import = kwargs.get('import', False)

        if self._import and name in environ:
            self.set_user_value(environ[name])

    def __del__(self):
        JConfigItem.__del__(self)


class JConfigTristate(JConfigItem):

    _DEFAULT_PROMPT = 'Use {0} (y/m/n)'
    _RANGE = ('y', 'm', 'n')
    _DEFAULT_HELP = [
        'No Help Message'
    ]

    def get_help(self):
        return self._help

    def get_prompt(self):
        return self._prompt

    def set_user_value(self, val):
        if val not in JConfigTristate._RANGE:
            raise ValueError('value should be one of (y/m/n)')
        JConfigItem.set_user_value(self, val)

    def __init__(self, name, var_pub, **kwargs):

        self._prompt = ""
        self._help = []
        self._import = False

        JConfigItem.__init__(self, name, 'tristate', var_pub, **kwargs)

        self._prompt = kwargs.get('prompt', JConfigTristate._DEFAULT_PROMPT.format(self._name))
        self._help = kwargs.get('help', JConfigTristate._DEFAULT_HELP)
        self._import = kwargs.get('import', False)

        if self._import and name in environ:
            self.set_user_value(environ[name])

    def __del__(self):
        JConfigItem.__del__(self)


class JConfigBool(JConfigItem):

    _DEFAULT_PROMPT = 'Use {0} (y/n)'
    _RANGE = ('y', 'n')
    _DEFAULT_HELP = [
        'No Help Message'
    ]

    def get_help(self):
        return self._help

    def get_prompt(self):
        return self._prompt

    def set_user_value(self, val):
        if val not in JConfigBool._RANGE:
            raise ValueError('value should be \'y\' or \'n\'')
        JConfigItem.set_user_value(self, val)

    def __init__(self, name, var_pub, **kwargs):
        self._prompt = ""
        self._help = []
        self._import = False

        JConfigItem.__init__(self, name, 'bool', var_pub, **kwargs)

        self._prompt = kwargs.get('prompt', JConfigBool._DEFAULT_PROMPT.format(self._name))
        self._help = kwargs.get('help', JConfigBool._DEFAULT_HELP)
        self._import = kwargs.get('import', False)

        if self._import and name in environ:
            self.set_user_value(environ[name])

    def __del__(self):
        JConfigItem.__del__(self)


class JConfigEnum(JConfigItem):

    _DEFAULT_PROMPT = 'Choose Option 0~{0} :'
    _DEFAULT_HELP = [
        'No Help Message'
    ]

    def __init__(self, name, var_pub, **kwargs):
        self._enum = []
        self._prompt = ''
        self._help = []
        self._import = False

        JConfigItem.__init__(self, name, 'enum', var_pub, **kwargs)

        self._type = 'enum'
        self._enum = kwargs.get('enum', [])
        self._prompt = kwargs.get('prompt', JConfigEnum._DEFAULT_PROMPT.format(len(self._enum)))
        self._help = kwargs.get('help', JConfigEnum._DEFAULT_HELP)
        self._import = kwargs.get('import', False)
        if self._import and name in environ:
            self.set_user_value(environ[name])

    def get_elements(self):
        return self._enum

    def get_help(self):
        return self._help

    def get_prompt(self):
        return self._prompt

    def set_user_value(self, val):
        ival = int(val)
        if len(self._enum) <= ival:
            raise ValueError('value shoud be within 0~{max}'.format(max=len(self._enum) - 1))
        JConfigItem.set_user_value(self, self._enum[ival])

    def __del__(self):
        JConfigItem.__del__(self)


class JConfigHex(JConfigItem):

    _DEFAULT_PROMPT = 'Input Hex Value for {}'
    _DEFAULT_HELP = [
        'No Help Message'
    ]

    def __init__(self, name, var_pub, **kwargs):
        self._prompt = ''
        self._help = []
        self._import = False
        self._range = []
        self._pattern = re.compile('0x[0-9a-fA-F]+')

        JConfigItem.__init__(self, name, 'hex', var_pub, **kwargs)

        self._prompt = kwargs.get('prompt', JConfigHex._DEFAULT_PROMPT.format(name))
        self._help = kwargs.get('help', JConfigHex._DEFAULT_HELP)
        self._import = kwargs.get('import', False)
        self._range = kwargs.get('range', [])
        for i in self._range:
            if not self._pattern.match(i):
                raise ValueError('value in range attribute should be formatted as \'0x[0-9a-fA-F]\'')

        self._range = [int(i, 16) for i in self._range]

        if self._import and name in environ:
            self.set_user_value(environ[name])

    def set_user_value(self, val):
        if not self._pattern.match(val):
            raise ValueError('value should be formatted as \'0x[0-9a-fA-F]\'')
        ival = int(val, 16)
        if len(self._range) > 1:
            if self._range[0] > ival or self._range[1] < ival:
                raise ValueError('value should be within 0x{min:x}~0x{max:x}'.format(min=self._range[0], max=self._range[1]))
        JConfigItem.set_user_value(self, val)

    def get_help(self):
        return self._help

    def get_prompt(self):
        return self._prompt

    def __del__(self):
        JConfigItem.__del__(self)


class JConfigInt(JConfigItem):

    _DEFAULT_PROMPT = 'Input Integer Value for {}'
    _DEFAULT_HELP = [
        'No Help Message'
    ]

    def __init__(self, name, var_pub, **kwargs):
        self._prompt = ''
        self._help = []
        self._import = False

        JConfigItem.__init__(self, name, 'int', var_pub, **kwargs)

        self._prompt = kwargs.get('prompt', JConfigInt._DEFAULT_PROMPT.format(name))
        self._help = kwargs.get('help', JConfigInt._DEFAULT_HELP)
        self._import = kwargs.get('import', False)
        self._range = kwargs.get('range', [])
        if self._import and name in environ:
            self.set_user_value(environ[name])

    def set_user_value(self, val):
        val = int(val)
        if len(self._range) > 1:
            if (val < self._range[0]) or (val > self._range[1]):
                raise ValueError('value should between {min} ~ {max}'.format(min=self._range[0], max=self._range[1]))
        JConfigItem.set_user_value(self, val)

    def get_help(self):
        return self._help

    def get_prompt(self):
        return self._prompt

    def __del__(self):
        JConfigItem.__del__(self)


class JConfigRecipe:

    def on_update_var(self, var, update_val):
        if var in self._var_map:
            self._var_map.update({var: update_val})
        if var in self._unresolved_path:
            self._unresolved_path.update({var: update_val})

    def __str__(self):
        self._path = self._var_pub.resolve_path(self._path)
        return 'include {}'.format(self._path)

    def __del__(self):
        if len(self._unresolved_path) > 0:
            for key in self._unresolved_path:
                self._var_pub.unsubscribe_variable_change(key)

    def __init__(self, name='recipe', var_pub=None, base_dir='./', var_map={}, **kwargs):
        self._name = name
        self._path = None
        self._var_pub = var_pub
        self._var_map = var_map
        self._base_dir = base_dir
        self._unresolved_path = {}

        if not isinstance(var_pub, ConfigVariableMonitor):
            raise TypeError('var_pub is not instance of {}'.format(str(ConfigVariableMonitor)))
        self._path = path.abspath(path.join(self._base_dir, kwargs.get('path', './Makefile')))

        for p in self._path.split('/'):
            if '$' in p:
                urpath = p.split('$')[1]
                if urpath in self._var_map:
                    self._unresolved_path.update({urpath: self._var_map[urpath]})
                else:
                    self._unresolved_path.update({urpath: ''})
                self._var_pub.subscribe_variable_change(urpath, self)


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
            raise FileNotExistError(_FILE_ERROR_FORMAT.format(config_file))
        self._jconfig_file = config_file
        self._base_dir = '/'.join(config_file.split('/')[:-1])    # extract base directory in which root config file is

    def get_childs(self):
        return self._child

    def get_items(self):
        return self._items

    def write_recipe(self, fp):
        if not isinstance(fp, file):
            return
        for recipe in self._recipes:
            fp.write('{}\n'.format(recipe))
        for child in self._child:
            child.write_recipe(fp)

    def is_visible(self):
        return self._visibility

    def parse(self):
        if len(self._unresolved_path) > 0:
            '''
            resolve path before opening the file
            '''
            for idx, pv in enumerate(self._unresolved_path):
                path_var = '$' + pv
                self._jconfig_file = self._jconfig_file.replace(path_var, self._unresolved_path[pv])

        if not path.exists(self._jconfig_file):
            raise FileNotExistError(_FILE_ERROR_FORMAT.format(self._jconfig_file))
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
                    config_path = self._base_dir + '.'.join(config_path.split('.')[1:])
                    self._child.append(JConfig(name=key, jconfig_file=config_path, **config_json[key]))
                elif 'recipe' in config_type:
                    self._recipes.append(JConfigRecipe(key, self._var_pub, self._base_dir, self._var_map,
                                                       **config_json[key]))

    def __str__(self):
        report_str = str('>>> Config : {}\n'.format(self._name))
        for item in self._items:
            report_str += str(item)
        report_str += '<<< Config : {}\n'.format(self._name)
        return report_str

    def __init__(self, name='root', jconfig_file='./config.json', var_map={}, parent=None, **kwargs):
        self._name = name
        self._jconfig_file = jconfig_file
        self._parent = parent
        self._var_map = var_map
        self._unresolved_path = {}
        self._base_dir = './'
        self._items = []
        self._child = []
        self._recipes = []
        self._visibility = True

        try:
            self._var_pub = ConfigVariableMonitor()
        except ConfigVariableMonitor as var_pub:
            self._var_pub = var_pub

        self._jconfig_file = jconfig_file
        self._depend = kwargs.get('depend', {})
        self._name = name
        self._var_pub.get_update(self._var_map)
        self._base_dir = '/'.join(jconfig_file.split('/')[:-1])

        if '$' in self._jconfig_file:
            '''
            unresolved part exists in config file path
            '''
            for p in self._jconfig_file.split('/'):
                if '$' in p:
                    path_var = p.split('$')[1]
                    if path_var in self._var_map:
                        self._unresolved_path.update({path_var: self._var_map[path_var]})
                    else:
                        self._unresolved_path.update({path_var: ''})
                    self._var_pub.subscribe_variable_change(path_var, self)
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


_TYPE_ERROR_FORMAT = '{0} should be instance of {1}'
_FILE_ERROR_FORMAT = '{0} doesn\'t exists'

TYPE, HELP, IMPORT, DEPEND, DEFAULT, PROMPT, PATH, \
     BOOL, TRISTATE, STRING, CONFIG, INT, HEX = range(13)


KW_REVMAP = {'type': TYPE, 'help': HELP, 'depend': DEPEND, 'default': DEFAULT,
             'prompt': PROMPT, 'path': PATH, 'bool': BOOL, 'tristate': TRISTATE,
             'string': STRING, 'config': CONFIG, 'int': INT, 'hex': HEX}

JCONFIG_HELP_STRING = '----------------------------------------------------\n' \
                      '*              jconfigpy {maj}.{minor}                       *\n' \
                      '*              {author}                            *\n' \
                      '----------------------------------------------------\n' \
                      '\n\n' \
                      '-c : -c initiate configuration\n' \
                      '-i [file] : define input file explicitly\n' \
                      '-u [t/g]  : set ui type for configuration (default text mode)\n' \
                      '-s [file] : load configuration from file\n'


def print_help(item):
    if not isinstance(item, JConfigItem):
        return
    for hdlin in item.get_help():
        print(hdlin)


def prompt_enum(item):
    if not isinstance(item, JConfigEnum):
        return
    if not item.is_visible():
        return
    print('\nCONFIG_{0}'.format(item.get_name()))
    elements = item.get_elements()
    for idx, ele in enumerate(elements):
        print('{0} {1}'.format(idx, ele))
    val = 'h'
    while val == 'h' or val == '':
        val = raw_input('{0} (0 ~ {1}) : '.format(item.get_prompt(), len(elements) - 1))
        if val == 'h':
            print_help(item)
        elif val == '':
            val = item.get_default_value()
            if val is not '':
                item.set_user_value(val)
        else:
            try:
                item.set_user_value(val)
            except ValueError as ve:
                val = 'h'
                print(ve)
    print('selected item is {}\n'.format(item.get_user_value()))


def prompt_bool(item):
    if not isinstance(item, JConfigBool):
        return
    if not item.is_visible():
        return
    print('\nCONFIG_{0}'.format(item.get_name()))
    val = 'h'
    while val == 'h' or val == '':
        val = raw_input('{0} : '.format(item.get_prompt()))
        if val == 'h':
            print_help(item)
        elif val == '':
            val = item.get_default_value()
            if val is not '':
                item.set_user_value(val)
        else:
            try:
                item.set_user_value(val)
            except ValueError as ve:
                val = 'h'
                print(ve)

    print('{0} is set to {1}'.format('CONFIG_' + item.get_name(), val))


def prompt_tristate(item):
    if not isinstance(item, JConfigTristate):
        return
    if not item.is_visible():
        return
    print('\nCONFIG_{0}'.format(item.get_name()))
    val = 'h'
    while val == 'h' or val == '':
        val = raw_input('{0} : '.format(item.get_prompt()))
        if val == 'h':
            print_help(item)
        elif val == '':
            val = item.get_default_value()
            if val is not '':
                item.set_user_value(val)
            else:
                print('No default value')
                print_help(item)
        else:
            try:
                item.set_user_value(val)
            except ValueError as ve:
                print(ve)
                val = 'h'

    print('{0} is set to {1}'.format('CONFIG_' + item.get_name(), val))


def prompt_string(item):
    if not isinstance(item, JConfigString):
        return
    if not item.is_visible():
        return
    print('\nCONFIG_{0}'.format(item.get_name()))
    val = 'h'
    while val == 'h' or val == '':
        val = raw_input('{0} : '.format(item.get_prompt()))
        if val == 'h':
            print_help(item)
        elif val == '':
            val = item.get_default_value()
            if val is not '':
                item.set_user_value(val)
            else:
                print('No default value')
                print_help(item)
        else:
            try:
                item.set_user_value(val)
            except ValueError as ve:
                print(ve)
                val = 'h'
    item.set_user_value(val)
    print('{0} is set to {1}'.format('COFNIG_{}'.format(item.get_name()), item.get_user_value()))


def prompt_int(item):
    if not isinstance(item, JConfigInt):
        return
    if not item.is_visible():
        return
    print('\nCONFIG_{0}'.format(item.get_name()))
    val = 'h'
    while val == 'h' or val == '':
        val = raw_input('{0} : '.format(item.get_prompt()))
        if val == 'h':
            print_help(item)
        elif val == '':
            val = item.get_default_value()
            if val is not '':
                item.set_user_value()
            else:
                print('No default value')
                print_help(item)
        else:
            try:
                item.set_user_value(val)
            except ValueError as ve:
                print(ve)
                val = 'h'

    print('entered value is {}\n'.format(item.get_user_value()))


def prompt_hex(item):
    if not isinstance(item, JConfigHex):
        return
    if item.is_visible():
        return
    print('\nCONFIG_{0}'.format(item.get_name()))
    val = 'h'
    while val == 'h' or val == '':
        val = raw_input('{0} : '.format(item.get_prompt()))
        if val == 'h':
            print_help(item)
        elif val == '':
            val = item.get_default_value()
            if val is not '':
                item.set_user_value(val)
            else:
                print('No default value')
                print_help(item)
        else:
            try:
                item.set_user_value(val)
            except ValueError as ve:
                print(ve)
                val = 'h'

    print('entered value is {}\n'.format(item.get_user_value()))


def prompt_config(config):
    if not isinstance(config, JConfig):
        return
    if not config.is_visible():
        return
    config.parse()
    for item in config.get_items():
        if item.is_visible():
            item_type = item.get_type()
            if item_type is 'enum':
                prompt_enum(item)
            elif item_type is 'int':
                prompt_int(item)
            elif item_type is 'hex':
                prompt_hex(item)
            elif item_type is 'bool':
                prompt_bool(item)
            elif item_type is 'tristate':
                prompt_tristate(item)
            elif item_type is 'string':
                prompt_string(item)

    for child in config.get_childs():
        prompt_config(child)


def init_text_mode_config(argv):
    file_name = None
    result_file = '.config'
    if '-i' not in argv:
        return
    for idx, arg in enumerate(argv):
        if '-i' in arg:
            if len(argv) <= idx + 1:
                return
            file_name = argv[idx + 1]
        if '-o' in arg:
            if len(argv) <= idx + 1:
                return
            result_file = argv[idx + 1]
    if not path.exists(file_name):
        raise FileNotExistError('File {} does not exist.'.format(file_name))
    root_config = JConfig(jconfig_file=file_name)
    prompt_config(root_config)

    try:
        monitor = ConfigVariableMonitor()
    except ConfigVariableMonitor as singleinstance:
        monitor = singleinstance

    with open(result_file, 'w+') as ofp:
        monitor.write(ofp)
        root_config.write_recipe(ofp)



def load_saved_config(argv):
    if '-i' not in argv:
        return


def main(argv=None):
    if argv is not None:
        for idx, arg in enumerate(argv):
            if '-h' in arg or '--help' in arg:
                print(JCONFIG_HELP_STRING.format(maj=0, minor=0, author='doowoong'))
                return
            elif '-c' in arg:
                if '-u' not in argv:
                    '''
                    configuration is performed with text based method
                    '''
                    init_text_mode_config(argv)
                else:
                    '''
                    ui type can be defined
                    '''
                    pass
                return
            elif '-s' in arg:
                load_saved_config(argv)
                return

    jconfig = JConfig(jconfig_file='example/config.json')
    jconfig.parse()
    print(jconfig)


if __name__ == '__main__':
    main(sys.argv)