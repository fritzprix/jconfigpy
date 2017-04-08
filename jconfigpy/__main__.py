#!/usr/bin/python
import sys

from Dialog import CMDDialog
from Config import JConfig
import jconfigpy

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



def main(argv=None):
    conf_dialog = CMDDialog()
    if argv is not None:
        for idx, arg in enumerate(argv):
            if '-h' in arg or '--help' in arg:
                print(JCONFIG_HELP_STRING.format(maj=0, minor=4, author='doowoong', email='innocentevil0914@gmail.com'))
                return
            elif '-c' in arg:
                if '-u' not in argv:
                    '''
                    configuration is performed with text based method
                    '''
                    jconfigpy.init_text_mode_config(argv, conf_dialog)
                else:
                    '''
                    ui type can be defined
                    '''
                    pass
                return
            elif '-s' in arg:
                jconfigpy.load_saved_config(argv, conf_dialog)
                return

    jconfig = JConfig(jconfig_file='../example/config.json')
    jconfig.parse()
    print(jconfig)


if __name__ == '__main__':
    main(sys.argv)
