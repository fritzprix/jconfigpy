import sys
import time
import json
import re
from os import path
from os import environ
import os
import random


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

    @staticmethod
    def rand(max_byte):
        if not max_byte > 0:
            raise ValueError('max_byte should be larger than 0')
        random.seed(os.urandom(64))
        msk = ((1 << (max_byte * 8)) - 1)
        return random.randint(msk, msk << 4) & msk

    @staticmethod
    def get_time():
        return  int(time.time())

    def is_forced(self):
        return self._isforced == 'y'

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
            self._visibility = self._var_pub.check_depend(**self._depend)
            return True
        return False

    def get_resolved_genlist(self):
        genlist = {}
        if not len(self._gen_list) > 0:
            return genlist
        to_int = self.to_int
        to_bool = self.to_bool
        to_tristate = self.to_tristate
        to_hex = self.to_hex
        to_string = self.to_string
        rand = JConfigItem.rand
        ctime = JConfigItem.get_time
        this = self.get_user_value()
        for key in self._gen_list:
            genlist.update({key: eval(self._gen_list[key])})
        return genlist

    def get_type(self):
        return self._type

    def is_visible(self):
        return self._visibility

    def to_hex(self, val):
        raise NotImplementedError(JConfigItem._NIE_MESSAGE.format(JConfigItem.to_hex))

    def to_int(self, val):
        raise NotImplementedError(JConfigItem._NIE_MESSAGE.format(JConfigItem.to_int))

    def to_bool(self, val):
        raise NotImplementedError(JConfigItem._NIE_MESSAGE.format(JConfigItem.to_bool))

    def to_tristate(self, val):
        raise NotImplementedError(JConfigItem._NIE_MESSAGE.format(JConfigItem.to_tristate))

    def to_string(self, val):
        raise NotImplementedError(JConfigItem._NIE_MESSAGE.format(JConfigItem.to_string))

    def __init__(self, name, type_, var_pub, **kwargs):
        self._user_val = None
        self._def_val = kwargs.get('default', '')
        self._var_pub = None
        self._name = name
        self._visibility = True
        self._depend = kwargs.get('depend', {})
        self._type = type_
        self._gen_list = kwargs.get('gen-list', {})
        self._isforced = kwargs.get('force', 'n')
        if self.is_forced() and self._def_val == '':
            raise ValueError(_VALUE_ERROR_FORMAT.format('default', 'not empty'))

        if not isinstance(var_pub, ConfigVariableMonitor):
            raise TypeError(_TYPE_ERROR_FORMAT.format('var_pub', ConfigVariableMonitor))
        self._var_pub = var_pub

        if len(self._depend) > 0:
            self._visibility = var_pub.check_depend(**self._depend)
            for var in enumerate(self._depend):
                self._var_pub.subscribe_variable_change(var, self)  # subscribe variable change

    def __str__(self):

        return JConfigItem._REPORT_FORMAT.format(name=self._name,
                                                 dval=self._def_val,
                                                 uval=self._user_val,
                                                 deplist=self._depend,
                                                 visible=self._visibility)

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

    def to_string(self, val):
        return val

    def get_help(self):
        return self._help

    def get_prompt(self):
        return self._prompt

    def set_user_value(self, val):
        if len(val) == 0:
            raise ValueError('string type should not be empty ')
        JConfigItem.set_user_value(self, val)

    def to_bool(self, val):
        if self.is_visible():
            return "y"
        else:
            return "n"

    def to_int(self, val):
        if self.is_visible():
            return int(val,0)
        else:
            return 0

    def to_hex(self, val):
        if self.is_visible():
            return "{:x}".format(int(val,16))
        else:
            return "0x00"

    def to_tristate(self, val):
        if self.is_visible():
            return "y"
        else:
            return "n"

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

    def to_tristate(self, val):
        return val

    def to_int(self, val):
        if val == "y":
            return 2
        elif val == "n":
            return 1
        return 0

    def to_hex(self, val):
        if val == "y":
            return "0x2"
        elif val == "n":
            return "0x1"
        return "0x0"

    def to_bool(self, val):
        if val == "y" or val == "m":
            return "y"
        return "n"

    def to_string(self, val):
        if val == "y":
            return "STATIC"
        elif val == "m":
            return "DYNAMIC"
        return "NONE"

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

    def to_bool(self, val):
        return val

    def to_string(self, val):
        if val == 'y':
            return "TRUE"
        return "FALSE"

    def to_hex(self, val):
        if val == 'y':
            return "0x01"
        return "0x00"

    def to_int(self, val):
        if val == 'y':
            return 1
        return 0

    def to_tristate(self, val):
        if val == 'y':
            return 'y'
        return 'n'

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

    def to_tristate(self, val):
        return "y"

    def to_int(self, val):
        return self._enum.index(val)

    def to_hex(self, val):
        return "{:x}".format(self.to_int(val))

    def to_string(self, val):
        return val

    def to_bool(self, val):
        return "y"

    def get_enum(self):
        return self._enum

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

    def to_bool(self, val):
        if int(val, 16) == 0:
            return "n"
        return "y"

    def to_int(self, val):
        return int(val, 16)

    def to_string(self, val):
        return val

    def to_tristate(self, val):
        if int(val, 16) == 0:
            return "n"
        return "y"

    def to_hex(self, val):
        return val

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
        _range = kwargs.get('range', [])
        for i in _range:
            if not self._pattern.match(i):
                raise ValueError('value in range attribute should be formatted as \'0x[0-9a-fA-F]\'')

        self._range = [int(i, 16) for i in _range]

        if self._import and name in environ:
            self.set_user_value(environ[name])

    def set_user_value(self, val):
        if not self._pattern.match(val):
            raise ValueError('value should be formatted as \'0x[0-9a-fA-F]\'')
        ival = int(val, 16)
        if len(self._range) > 1:
            if self._range[0] > ival or self._range[1] < ival:
                raise ValueError('value should be within 0x{min:x}~0x{max:x}'.format(min=self._range[0],
                                                                                     max=self._range[1]))
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

    def to_tristate(self, val):
        if val == 0:
            return "n"
        return "y"

    def to_string(self, val):
        return str(val)

    def to_bool(self, val):
        if val == 0:
            return "n"
        return "y"

    def to_hex(self, val):
        return "{:x}".format(val)

    def to_int(self, val):
        return val

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

    def get_resolved_path(self):
        return self._var_pub.resolve_path(self._path)

    def __del__(self):
        if len(self._unresolved_path) > 0:
            for key in self._unresolved_path:
                self._var_pub.unsubscribe_variable_change(key)

    def __init__(self, name='recipe', var_pub=None, base_dir='./', var_map=None, **kwargs):
        self._name = name
        self._path = None
        self._var_pub = var_pub
        self._var_map = dict(iterable=var_map)
        self._base_dir = base_dir
        self._unresolved_path = {}

        if not isinstance(var_pub, ConfigVariableMonitor):
            raise TypeError('var_pub is not instance of {}'.format(str(ConfigVariableMonitor)))
        self._path = path.abspath(path.join(self._base_dir, kwargs.get('path', './Makefile')))

        if '$' in self._path:
            head, tail = path.split(self._path)
            while tail != '':
                if '$' in tail:
                    urpath = tail.split('$')[1]
                    if urpath in self._var_map:
                        self._unresolved_path.update({urpath: self._var_map[urpath]})
                    else:
                        self._unresolved_path.update({urpath: ''})
                    self._var_pub.subscribe_variable_change(urpath, self)
                head, tail = path.split(head)


class JConfigRepo:

    LIB_DIR=[]

    def on_update_var(self, var, update_val):

        if var in self._var_map:
            self._var_map.update({var : update_val})
        if var in self._unresolved_path:
            self._unresolved_path.update({var: update_val})

    def get_resolved_path(self):
        return self._var_pub.resolve_path(self._path)

    @staticmethod
    def build_repo(**kwargs):
        make_cmd = kwargs.get('buildcmd')
        for cmd in make_cmd:
            os.system(cmd)

    def copy_output(self, out):
        os.system('cp {0} {1}'.format(path.join(self._path,out),self._out_path))


    def resolve_repo(self):
        print('Url : {0} / Path : {1}'.format(self._url, self._path))
        if not path.exists(self._path):
            os.system('git clone {0} {1}'.format(self._url, self._path))
        os.chdir(self._path)
        if not path.exists(self._pkg):
            raise FileNotExistError('File {} doesn\'t exists'.format(self._pkg))
        with open(self._pkg ,'r') as fp:
            package_json = json.load(fp,encoding='utf-8')
            if package_json['name'] != self._name:
                raise ValueError('Unexpected Package name : {}'.format(package_json['name']))
            JConfigRepo.build_repo(**package_json)
            package_headers =  package_json['include']
            package_inc = ''
            output_inc = ''
            output = package_json['output']
            version = package_json['version']
        os.chdir('../')
        for inc in package_headers:
            package_inc += 'INC-y+={0}\n'.format(path.abspath(path.join(self._path, inc)))
        if not path.exists(self._out_path):
            print self._out_path
            os.mkdir(self._out_path)
        for out in output:
            self.copy_output(out)
            if '.a' in out:
                output_inc += 'SLIB-y+={0}\n'.format(out)
            elif '.so' in out:
                output_inc += 'DLIB-y+={0}\n'.format(out)
        with open('autorecipe.mk','a+') as fp:
            fp.write(output_inc)
            fp.write(package_inc)
            fp.write('REPO-y+={0}\n'.format(self._path))
            if self._out_path not in JConfigRepo.LIB_DIR:
                JConfigRepo.LIB_DIR.append(self._out_path)
                fp.write('LDIR-y+={0}\n'.format(self._out_path))
        os.chdir(self._root_dir)


    def __del__(self):
        if len(self._unresolved_path) > 0:
            for key in self._unresolved_path:
                self._var_pub.unsubscribe_variable_change(key)


    def __init__(self, name='repo', var_pub=None, base_dir='./', root_dir = None , var_map=None, **kwargs):
        self._name = name
        self._path = None
        self._pkg = kwargs.get('pkg','package.json')
        self._var_pub = var_pub
        self._base_dir = base_dir
        self._root_dir = root_dir
        self._var_map = dict(iterable=var_map)
        self._unresolved_path = {}
        self._url = kwargs.get('url')
        self._out_path = path.abspath(path.join(self._base_dir,kwargs.get('out','./dep/')))

        if not isinstance(var_pub, ConfigVariableMonitor):
            raise TypeError('var_pub is not instance if {}'.format(str(ConfigVariableMonitor)))
        self._path = path.abspath(path.join(self._base_dir,self._name))

        if '$' in self._path:
            head, tail = path.split(self._path)
            while tail != '':
                if '$' in tail:
                    urpath = tail.split('$')[1]
                    if urpath in self._var_map:
                        self._unresolved_path.update({urpath: self._var_map[urpath]})
                    else:
                        self._unresolved_path.update({urpath: ''})
                    self._var_pub.subscribe_variable_change(urpath, self)
                head, tail = path.split(head)



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
                    config_path = path.abspath(path.join(self._base_dir, config_path))
                    self._child.append(JConfig(name=key, jconfig_file=config_path, root_dir=self._root, **config_json[key]))
                elif 'recipe' in config_type:
                    self._recipes.append(JConfigRecipe(key, self._var_pub, self._base_dir, self._var_map,**config_json[key]))
                elif 'repo' in config_type:
                    repositoy = JConfigRepo( var_pub=self._var_pub,base_dir=self._base_dir,root_dir=self._root,var_map=self._var_map,**config_json[key])
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

    def __init__(self, name='root', jconfig_file='./config.json', root_dir = None, var_map=None, parent=None, **kwargs):
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
            self._var_pub = ConfigVariableMonitor()
        except ConfigVariableMonitor as var_pub:
            self._var_pub = var_pub

        self._depend = kwargs.get('depend', {})
        self._name = name
        self._var_pub.get_update(self._var_map)
        self._base_dir = path.abspath(path.abspath(path.dirname(jconfig_file)))
        self._jconfig_file = path.abspath(jconfig_file)
        autogen_file = path.abspath(path.join(self._base_dir,'./autorecipe.mk'))
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


_TYPE_ERROR_FORMAT = '{0} should be instance of {1}'
_VALUE_ERROR_FORMAT = '{0} should be {1}'
_FILE_ERROR_FORMAT = '{0} doesn\'t exists'

TYPE, HELP, IMPORT, DEPEND, DEFAULT, PROMPT, PATH, \
     BOOL, TRISTATE, STRING, CONFIG, INT, HEX = range(13)


KW_REVMAP = {'type': TYPE, 'help': HELP, 'depend': DEPEND, 'default': DEFAULT,
             'prompt': PROMPT, 'path': PATH, 'bool': BOOL, 'tristate': TRISTATE,
             'string': STRING, 'config': CONFIG, 'int': INT, 'hex': HEX}

JCONFIG_HELP_STRING = '---------------------------------------------------------\n' \
                      '*\t\tjconfigpy {maj}.{minor}\t\t\t\t*\n' \
                      '*\t{author}({email})\t\t*\n' \
                      '---------------------------------------------------------\n' \
                      '\n\n' \
                      '-c : -c initiate configuration\n' \
                      '-i [file] : define input file explicitly\n' \
                      '-o [file] : output configuration file\n' \
                      '-u [t/g]  : set ui type for configuration (default text mode)\n' \
                      '-s [file] : load configuration from file\n' \
                      '-g [file] : specify name of header file for preprocessor macro\n' \
                      '-t [file] : specify template config file\n' \
                      '\n' \
                      '\n' \
                      'initiate configuration in command line\n' \
                      'ex) python jconfigpy.py -c -ut -i config.json -o .config\n' \
                      '\n' \
                      'initiate configuration from pre defined(stored) configuration\n' \
                      'ex) python jconfigpy.py -s -i .config -t config.json -o .new_config\n' \
                      '\n' \


def print_help(item):
    if not isinstance(item, JConfigItem):
        return
    for hdlin in item.get_help():
        print(hdlin)


def prompt_enum(item, predef={}):
    if not isinstance(item, JConfigEnum):
        return
    if not item.is_visible():
        return
    if item.is_forced():
        item.set_user_value(item.get_default_value())
        return
    name = item.get_name()
    if name in predef:
        estr = predef[name]
        idx = item._enum.index(estr)
        item.set_user_value(idx)
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


def prompt_bool(item, predef={}):
    if not isinstance(item, JConfigBool):
        return
    if not item.is_visible():
        return
    if item.is_forced():
        item.set_user_value(item.get_default_value())
        return
    name = item.get_name()
    if name in predef:
        item.set_user_value(predef[name])
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


def prompt_tristate(item, predef={}):
    if not isinstance(item, JConfigTristate):
        return
    if not item.is_visible():
        return
    if item.is_forced():
        item.set_user_value(item.get_default_value())
        return
    name = item.get_name()
    if name in predef:
        item.set_user_value(predef[name])
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


def prompt_string(item, predef={}):
    if not isinstance(item, JConfigString):
        return
    if not item.is_visible():
        return
    if item.is_forced():
        item.set_user_value(item.get_default_value())
        return
    name = item.get_name()
    if name in predef:
        item.set_user_value(predef[name])
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


def prompt_int(item, predef={}):
    if not isinstance(item, JConfigInt):
        return
    if not item.is_visible():
        return
    if item.is_forced():
        item.set_user_value(item.get_default_value())
        return
    name = item.get_name()
    if name in predef:
        item.set_user_value(predef[name])
        return
    print('\nCONFIG_{0}'.format(item.get_name()))
    val = 'h'
    while val == 'h' or val == '':
        val = raw_input('{0} : '.format(item.get_prompt()))
        if val == 'h':
            print_help(item)
        elif val == '':
            val = item.get_default_value()
            print(val)
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


def prompt_hex(item, predef={}):
    if not isinstance(item, JConfigHex):
        return
    if not item.is_visible():
        return
    if item.is_forced():
        item.set_user_value(item.get_default_value())
        return
    name = item.get_name()
    if name in predef:
        item.set_user_value(predef[name])
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


def prompt_config(config, predef={}):
    if not isinstance(config, JConfig):
        return
    if not config.is_visible():
        return
    config.parse()
    for item in config.get_items():
        if item.is_visible():
            item_type = item.get_type()
            if item_type is 'enum':
                prompt_enum(item, predef)
            elif item_type is 'int':
                prompt_int(item, predef)
            elif item_type is 'hex':
                prompt_hex(item, predef)
            elif item_type is 'bool':
                prompt_bool(item, predef)
            elif item_type is 'tristate':
                prompt_tristate(item, predef)
            elif item_type is 'string':
                prompt_string(item, predef)

    for child in config.get_childs():
        prompt_config(child, predef)


def init_text_mode_config(argv):
    file_name = None
    result_file = '.config'
    autogen_header = 'autogen.h'
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
        if '-g' in arg:
            if len(argv) <= idx + 1:
                return
            autogen_header = argv[idx + 1]

    if not path.exists(file_name):
        raise FileNotExistError('File {} does not exist.'.format(file_name))

    root_config = JConfig(jconfig_file=file_name,root_dir=path.abspath('./'))
    prompt_config(root_config)

    try:
        monitor = ConfigVariableMonitor()
    except ConfigVariableMonitor as singleinstance:
        monitor = singleinstance

    with open(result_file, 'w+') as ofp:
        monitor.write(ofp)
        root_config.write_recipe(ofp)
        ofp.write('\nDEF+=')
        root_config.write_genlist(ofp, ' {0}={1}')
        ofp.write('\n')

    with open(autogen_header, 'w+') as agen:
        agen.write('#ifndef ___AUTO_GEN_H\n')
        agen.write('#define ___AUTO_GEN_H\n')

        root_config.write_genlist(agen)

        agen.write('#endif\n')


def load_saved_config(argv):
    if '-i' not in argv:
        return
    config_file = './config.json'
    sconfig_file = None
    result_file = './.config'
    gen_file = './autogen.h'
    for idx, arg in enumerate(argv):
        if '-i' in arg:
            '''
            input configuration file (saved .config)
            '''
            if len(argv) <= idx + 1:
                return
            sconfig_file = argv[idx + 1]
        if '-t' in arg:
            '''
            config template file (root config.json)
            '''
            if len(argv) <= idx + 1:
                return
            config_file = argv[idx + 1]
        if '-o' in arg:
            '''
            output configuratoin file (target .config)
            '''
            if len(argv) <= idx + 1:
                return
            result_file = argv[idx + 1]
        if '-g' in arg:
            '''
            auto-generated file
            '''
            if len(argv) <= idx + 1:
                return
            gen_file = argv[idx + 1]

    if sconfig_file is None:
        return

    kv_map = {}
    with open(sconfig_file, 'r') as fp:
        for flin in fp:
            if 'CONFIG_' in flin:
                lin = flin.split('CONFIG_')[1]
                kv = lin.split('=')
                kv_map.update({kv[0]: kv[1]})
    print(kv_map)
    klist = []
    vlist = []
    for key in kv_map:
        klist.append(key)
        vlist.append(kv_map[key].split('\n')[0])
    kv_map = dict(zip(klist, vlist))
    root_config = JConfig(jconfig_file=config_file,root_dir=path.abspath('./'))
    prompt_config(root_config, kv_map)

    try:
        monitor = ConfigVariableMonitor()
    except ConfigVariableMonitor as singleinstance:
        monitor = singleinstance

    with open(result_file, 'w+') as ofp:
        monitor.write(ofp)
        root_config.write_recipe(ofp)
        ofp.write('\nDEF+=')
        root_config.write_genlist(ofp, ' {0}={1}')
        ofp.write('\n')

    with open(gen_file, 'w+') as agen:
        agen.write('#ifndef ___AUTO_GEN_H\n')
        agen.write('#define ___AUTO_GEN_H\n')

        root_config.write_genlist(agen)

        agen.write('#endif\n')


def main(argv=None):
    if argv is not None:
        for idx, arg in enumerate(argv):
            if '-h' in arg or '--help' in arg:
                print(JCONFIG_HELP_STRING.format(maj=0, minor=4, author='doowoong',email='innocentevil0914@gmail.com'))
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
