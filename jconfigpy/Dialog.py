from Config import JConfig
from Config import JConfigEnum
from Config import JConfigInt
from Config import JConfigString
from Config import JConfigHex
from Config import JConfigBool
from Config import JConfigTristate

from Item import JConfigItem


class Dialog:

    def __init__(self):
        pass

    @staticmethod
    def prompt_config(config, pre_def=None):
        pass


class CMDDialog(Dialog):

    def __init__(self):
        Dialog.__init__(self)

    @staticmethod
    def prompt_config(config, pre_def=None):
        assert isinstance(config, JConfig)
        if not config.is_visible():
            return
        config.parse()
        for item in config.get_items():
            if item.is_visible():
                item_type = item.get_type()
                if item_type is 'enum':
                    CMDDialog.prompt_enum(item, pre_def)
                elif item_type is 'int':
                    CMDDialog.prompt_int(item, pre_def)
                elif item_type is 'hex':
                    CMDDialog.prompt_hex(item, pre_def)
                elif item_type is 'bool':
                    CMDDialog.prompt_bool(item, pre_def)
                elif item_type is 'tristate':
                    CMDDialog.prompt_tristate(item, pre_def)
                elif item_type is 'string':
                    CMDDialog.prompt_string(item, pre_def)

        for child in config.get_childs():
            child_dialog = CMDDialog()
            child_dialog.prompt_config(child, pre_def)

    @staticmethod
    def print_help(item):
        if not isinstance(item, JConfigItem):
            return
        for hdlin in item.get_help():
            print(hdlin)

    @staticmethod
    def prompt_enum(item, predef=None):
        if not isinstance(item, JConfigEnum):
            return
        if not item.is_visible():
            return
        if item.is_forced():
            item.set_user_value(item.get_default_value())
            return
        name = item.get_name()
        if (predef is not None) and (name in predef):
            estr = predef[name]
            idx = item.get_enum().index(estr)
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
                CMDDialog.print_help(item)
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

    @staticmethod
    def prompt_bool(item, predef=None):
        if not isinstance(item, JConfigBool):
            return
        if not item.is_visible():
            return
        if item.is_forced():
            item.set_user_value(item.get_default_value())
            return
        name = item.get_name()
        if (predef is not None) and (name in predef):
            item.set_user_value(predef[name])
            return
        print('\nCONFIG_{0}'.format(item.get_name()))
        val = 'h'
        while val == 'h' or val == '':
            val = raw_input('{0} : '.format(item.get_prompt()))
            if val == 'h':
                CMDDialog.print_help(item)
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

    @staticmethod
    def prompt_tristate(item, predef=None):
        if not isinstance(item, JConfigTristate):
            return
        if not item.is_visible():
            return
        if item.is_forced():
            item.set_user_value(item.get_default_value())
            return
        name = item.get_name()
        if (predef is not None) and (name in predef):
            item.set_user_value(predef[name])
            return
        print('\nCONFIG_{0}'.format(item.get_name()))
        val = 'h'
        while val == 'h' or val == '':
            val = raw_input('{0} : '.format(item.get_prompt()))
            if val == 'h':
                CMDDialog.print_help(item)
            elif val == '':
                val = item.get_default_value()
                if val is not '':
                    item.set_user_value(val)
                else:
                    print('No default value')
                    CMDDialog.print_help(item)
            else:
                try:
                    item.set_user_value(val)
                except ValueError as ve:
                    print(ve)
                    val = 'h'

        print('{0} is set to {1}'.format('CONFIG_' + item.get_name(), val))

    @staticmethod
    def prompt_string(item, predef=None):
        if not isinstance(item, JConfigString):
            return
        if not item.is_visible():
            return
        if item.is_forced():
            item.set_user_value(item.get_default_value())
            return
        name = item.get_name()
        if (predef is not None) and (name in predef):
            item.set_user_value(predef[name])
            return
        print('\nCONFIG_{0}'.format(item.get_name()))
        val = 'h'
        while val == 'h' or val == '':
            val = raw_input('{0} : '.format(item.get_prompt()))
            if val == 'h':
                CMDDialog.print_help(item)
            elif val == '':
                val = item.get_default_value()
                if val is not '':
                    item.set_user_value(val)
                else:
                    print('No default value')
                    CMDDialog.print_help(item)
            else:
                try:
                    item.set_user_value(val)
                except ValueError as ve:
                    print(ve)
                    val = 'h'
        item.set_user_value(val)
        print('{0} is set to {1}'.format('COFNIG_{}'.format(item.get_name()), item.get_user_value()))

    @staticmethod
    def prompt_int(item, predef=None):
        if not isinstance(item, JConfigInt):
            return
        if not item.is_visible():
            return
        if item.is_forced():
            item.set_user_value(item.get_default_value())
            return
        name = item.get_name()
        if (predef is not None) and (name in predef):
            item.set_user_value(predef[name])
            return
        print('\nCONFIG_{0}'.format(item.get_name()))
        val = 'h'
        while val == 'h' or val == '':
            val = raw_input('{0} : '.format(item.get_prompt()))
            if val == 'h':
                CMDDialog.print_help(item)
            elif val == '':
                val = item.get_default_value()
                print(val)
                if val is not '':
                    item.set_user_value(val)
                else:
                    print('No default value')
                    CMDDialog.print_help(item)
            else:
                try:
                    item.set_user_value(val)
                except ValueError as ve:
                    print(ve)
                    val = 'h'

        print('entered value is {}\n'.format(item.get_user_value()))

    @staticmethod
    def prompt_hex(item, predef=None):
        if not isinstance(item, JConfigHex):
            return
        if not item.is_visible():
            return
        if item.is_forced():
            item.set_user_value(item.get_default_value())
            return
        name = item.get_name()
        if (predef is not None) and (name in predef):
            item.set_user_value(predef[name])
            return
        print('\nCONFIG_{0}'.format(item.get_name()))
        val = 'h'
        while val == 'h' or val == '':
            val = raw_input('{0} : '.format(item.get_prompt()))
            if val == 'h':
                CMDDialog.print_help(item)
            elif val == '':
                val = item.get_default_value()
                if val is not '':
                    item.set_user_value(val)
                else:
                    print('No default value')
                    CMDDialog.print_help(item)
            else:
                try:
                    item.set_user_value(val)
                except ValueError as ve:
                    print(ve)
                    val = 'h'

        print('entered value is {}\n'.format(item.get_user_value()))
