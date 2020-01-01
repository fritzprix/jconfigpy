import json
from os import path
import os
from ErrorType import FileNotExistError
from VariableMonitor import Monitor


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
        self._var_map = dict(var_map)
        self._base_dir = base_dir
        self._unresolved_path = {}

        if not isinstance(var_pub, Monitor):
            raise TypeError('var_pub is not instance of {}'.format(str(Monitor)))
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

    LIB_DIR = []

    def on_update_var(self, var, update_val):

        if var in self._var_map:
            self._var_map.update({var: update_val})
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
        os.system('cp {0} {1}'.format(path.join(self._path, out), self._out_path))

    def resolve_repo(self):
        if len(self._unresolved_path) > 0:
            for idx, pv in enumerate(self._unresolved_path):
                path_var = '$' + pv
                self._path = self._path.replace(path_var, self._unresolved_path[pv])
                self._out_path = self._out_path.replace(path_var, self._unresolved_path[pv])

        print('Url : {0} / Path : {1}'.format(self._url, self._path))
        if not path.exists(self._path):
            os.system('git clone {0} {1}'.format(self._url, self._path))
        if not path.exists(self._path):
            raise FileNotExistError('Git operation fail {}'.format(self._url))
        os.chdir(self._path)
        if path.abspath(os.curdir) != self._path:
            raise OSError('chdir doesn\'t work curdir : {}'.format(path.abspath(os.curdir)))
        if not path.exists(self._pkg):
            raise FileNotExistError('File {} doesn\'t exists'.format(self._pkg))
        package_headers = None
        package_inc = None
        output = None
        output_inc = None
        with open(self._pkg, 'r') as fp:
            package_json = json.load(fp, encoding='utf-8')
            if package_json['name'] != self._name:
                raise ValueError('Unexpected Package name : {}'.format(package_json['name']))
            JConfigRepo.build_repo(**package_json)
            package_headers = package_json['include']
            package_inc = ''
            output_inc = ''
            output = package_json['output']
            # version = package_json['version']
        assert package_headers is not None
        assert package_inc is not None
        assert output is not None
        assert output_inc is not None
        os.chdir('../')
        for inc in package_headers:
            package_inc += 'INC-y+={0}\n'.format(path.abspath(path.join(self._path, inc)))
        if not path.exists(self._out_path):
            os.mkdir(self._out_path)
        for out in output:
            self.copy_output(out)
            if '.a' in out:
                output_inc += 'SLIB-y+={0}\n'.format(out)
            elif '.so' in out:
                output_inc += 'DLIB-y+={0}\n'.format(out)
        with open('autorecipe.mk', 'a+') as fp:
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

    def __init__(self, name='repo', var_pub=None, base_dir='./', root_dir=None, var_map=None, **kwargs):
        self._name = name
        self._path = None
        self._pkg = kwargs.get('pkg', 'package.json')
        self._var_pub = var_pub
        self._base_dir = base_dir
        self._root_dir = root_dir
        self._var_map = dict(var_map)
        self._unresolved_path = {}
        self._url = kwargs.get('url')
        self._out_path = path.abspath(path.join(self._base_dir, kwargs.get('out', './dep/')))

        if not isinstance(var_pub, Monitor):
            raise TypeError('var_pub is not instance if {}'.format(str(Monitor)))
        self._path = path.abspath(path.join(self._base_dir, self._name))

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
