from os import path
from Dialog import Dialog
from Dialog import CMDDialog
from ErrorType import FileNotExistError
from VariableMonitor import Monitor
from Config import JConfig


def init_text_mode_config(argv, config_dialog):
    file_name = None
    assert isinstance(config_dialog, Dialog)
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
        raise FileNotExistError(file_name)

    root_config = JConfig(jconfig_file=file_name, root_dir=path.abspath('./'))
    config_dialog.prompt_config(root_config)

    try:
        monitor = Monitor()
    except Monitor as single_instance:
        monitor = single_instance

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


def load_saved_config(argv, dialog):
    if '-i' not in argv:
        return
    assert isinstance(dialog, Dialog)
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
    dialog.prompt_config(root_config, kv_map)

    try:
        monitor = Monitor()
    except Monitor as single_instance:
        monitor = single_instance

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

if __name__ == '__main__':
    print 'hello'