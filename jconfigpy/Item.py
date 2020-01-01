import os
import random
import re
import time
from os import environ

import VariableMonitor


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
        return int(time.time())

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
        no_opt = (to_int,
                  to_bool,
                  this,
                  ctime,
                  rand,
                  to_string,
                  to_hex,
                  to_tristate)
        assert no_opt[0] is not None
        assert no_opt[-1] is not None
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
        if self.is_forced():
            assert self._def_val != ''
        assert isinstance(var_pub, VariableMonitor.Monitor)
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
        return '\"{}\"'.format(val)

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
            return int(val, 0)
        else:
            return 0

    def to_hex(self, val):
        if self.is_visible():
            return "{:x}".format(int(val, 16))
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
        return '\"{}\"'.format(val)

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