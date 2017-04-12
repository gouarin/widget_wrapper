import inspect
from collections import OrderedDict
from traits2cpp import traits2cpp
import os

def get_class_info(klass):
    classname = klass.__name__
    s = klass.__module__.split('.')
    return {'filename': '/'.join(s), 'classname': classname}

class wrapper:
    def __init__(self, module, traits2lang = traits2cpp, output=None):
        self.prefix = '.hpp'
        self.file2wrap = None
        self.ouput = None

        self.inspect_module(module)
        self.build_output(traits2lang)

    def inspect_module(self, module):
        """
        inspect the module to wrap.

        construct the class2wrap attribute in the following way

        filename: {classname: {'attr': [(attribute name, default value), ...],
                              'base': [{'filename': filename, 'classname': classname}, ...],
                             }
                  }
        """

        mod = __import__(module)
        self.file2wrap = OrderedDict()
        for d in dir(mod):
            component = eval('mod.' + d)
            if inspect.isclass(component):
                # check if component is in the module
                if component.__module__.split('.')[0] == module:
                    info = get_class_info(component)
                    # check the traits types for this class
                    if getattr(component, 'class_own_traits', None):
                        attr = OrderedDict()
                        for k, v in component.class_own_traits().items():
                            # check if we have to observe this attribute
                            if v.metadata.get('sync', False):
                                if isinstance(v.default_value, str):
                                    default_value = '"%s"'%v.default_value
                                else:
                                    default_value = v.default_value
                                attr[k] = (v.__class__.__name__, default_value)
                        filename = info['filename']
                        self.file2wrap[filename] = self.file2wrap.get(filename, []) + [{d: {'attr': attr,
                                                         'base': [get_class_info(base) for base in component.__bases__]
                                                   }}]

    def build_output(self, traits2lang):
        self.output = []
        for filename, classes in self.file2wrap.items():
            klass = {}
            dependencies = set()
            for cl in classes:
                for classname, classdata in cl.items():
                    tmp = OrderedDict()
                    #tmp['classname'] = classname
                    ltmp = []
                    for varname, vardata in classdata['attr'].items():
                        traits = traits2lang.get(vardata[0], None)
                        dep = None
                        if isinstance(traits, tuple):
                            dep = traits[1]
                            traits = traits[0]
                        ltmp.append({'name': varname, 'type': traits, 'default_value': vardata[1]})
                        if dep:
                            dependencies = dependencies.union({dep})            
                    tmp['attr'] = ltmp
                    tmp['inheritance'] = [i['classname'] for i in classdata['base']]
                    dependencies = dependencies.union(set([i['filename']+self.prefix for i in classdata['base']]))
                    klass[classname] = tmp
            # remove the dependency of the same file
            dependencies = sorted(dependencies - {filename+self.prefix})
            self.output.append((filename, dependencies, klass))
        
    def build_files(self, template, path='output', prefix='.hpp'):
        from jinja2 import Environment, PackageLoader, select_autoescape
        env = Environment(
            loader=PackageLoader('wrapper', 'templates'),
            autoescape=select_autoescape(['tmpl'])
        )
        template = env.get_template(template)

        for r in self.output:
            filename, dependencies, class2wrap = r
            output_file = path + '/' + filename + prefix
            dirname = os.path.dirname(os.path.abspath(output_file))

            if not os.path.exists(dirname):
                os.makedirs(dirname)

            # reorder class in filename to have good order dependencies
            classinfile = {c: 0 for c in class2wrap}
            def get_order(classinfile, klass, class2wrap):
                for inheritance in klass['inheritance']:
                    if classinfile.get(inheritance, None) is not None:
                        classinfile[inheritance] += 1
                        get_order(classinfile, class2wrap[inheritance], class2wrap)

            for c in class2wrap:
                get_order(classinfile, class2wrap[c], class2wrap)
                        
            import operator
            sorted_x = sorted(classinfile.items(), key=operator.itemgetter(1))

            klass = OrderedDict()
            for s in sorted_x[-1::-1]:
                klass[s[0]] = class2wrap[s[0]]

            # generate files for the specified language
            with open(output_file, 'w') as f:
                f.write(template.render(dependencies=dependencies, klass=klass))

#w = wrapper('pythreejs')
w = wrapper('bqplot')
w.build_files('cpp.tmpl')
