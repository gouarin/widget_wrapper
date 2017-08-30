import inspect
from collections import OrderedDict
from traits2cpp import traits2cpp, classLink
import os
from traitlets import (
        Int, Unicode, List, Enum, Dict, Bool, Float, Instance, Tuple,
        TraitError, validate, Undefined
    )
from traittypes import Array

def get_class_info(module_name, klass):
    """
    from a Python class return the name of the class as string 
    and the path.
    """
    classname = klass.__name__
    if classLink.get(classname, None):
        return classLink[classname]
    s = klass.__module__.replace(module_name + '.', '', 1)
    return {'filename': s, 'classname': classname}

def python2cpp_classname(klass, prefix=''):
    """
    Change the string format of a Python class name.

    For example
    
        - Class -> class
        - ClassAAA -> class_aaa
        - OtherLongClassName -> other_long_class_name

    """
    new_klass = prefix + klass[0].lower()
    for i in range(1, len(klass)):
        c = klass[i]
        if c.isupper():
            if not klass[i-1].isupper():
                new_klass += '_' + c.lower()
            else:
                new_klass += c.lower() 
        else:
            new_klass += c.lower()
    return new_klass

def get_default_value(v):
    """
    Return the default value of a traitlets type.
    """
    if isinstance(v.default_value, str):
        return '"%s"'%v.default_value
    elif v.default_value == Undefined:
        return None
    else:
        return v.default_value

def is_optional(v):
    """
    Check if a traitlets instance is optional.
    """
    if v.allow_none:
        return True
    return False

def get_enum_value(v):
    """
    return all the enum values.
    """
    if isinstance(v, Enum):
        return v.values
    return None

def get_trait(type_name, traits2lang, own_classes):
    if own_classes.get(type_name, None):
        return 'xw::xholder<x{}>'.format(own_classes[type_name])
    trait = traits2lang.get(type_name, None)
    if isinstance(trait, dict):
        return trait['type']
    else:
        return trait

def get_dep(type_name, traits2lang, own_classes):
    if own_classes.get(type_name, None):
        return own_classes[type_name] + '.hpp'
    trait = traits2lang.get(type_name, None)
    if isinstance(trait, dict):
        return trait.get('include', None)
    return None

def get_using(type_name, traits2lang):
    trait = traits2lang.get(type_name, None)
    if isinstance(trait, dict):
        if 'using' in trait:
            return trait['type'] + ' = ' + trait['using']
    return None

class wrapper:
    def __init__(self, module, namespace, package_name, traits2lang = traits2cpp):
        self.prefix = '.hpp'
        self.output = None
        self.file2wrap = None
        self.module = module

        self.namespace = namespace
        self.package_name = package_name

        self.inspect_module()
        self.build_output(traits2lang)

    def inspect_module(self):
        """
        inspect the module to wrap.

        construct the class2wrap attribute in the following way

        filename: {classname: {'attr': [(attribute name, default value), ...],
                              'base': [{'filename': filename, 'classname': classname}, ...],
                             }
                  }
        """

        mod = __import__(self.module)
        self.file2wrap = OrderedDict()
        for d in dir(mod):
            component = eval('mod.' + d)
            if inspect.isclass(component):
                # check if component is in the module
                if component.__module__.split('.')[0] == self.module:
                    info = get_class_info(self.module, component)
                    # check the traits types for this class
                    if getattr(component, 'class_own_traits', None):
                        attr = OrderedDict()
                        for k, v in component.class_own_traits().items():
                            if not k.startswith('_'):
                                # check if we have to observe this attribute
                                if v.metadata.get('sync', False):
                                    default_value = get_default_value(v)
                                    optional = is_optional(v)
                                    enum = get_enum_value(v)
                                    if isinstance(v, Tuple):
                                        default_value = 'pair_type' + str(v.default_args[0])
                                    if isinstance(v, List):
                                        if v._trait:
                                            if v._trait.__class__.__name__ == 'Instance':
                                                element_type = v._trait.klass.__name__
                                            else:
                                                element_type = v._trait.__class__.__name__
                                        type_ = ('List', element_type)
                                    else:
                                        if v.__class__.__name__ == 'Instance':
                                            type_ = v.klass.__name__
                                        else:
                                            type_ = v.__class__.__name__
                                    attr[k] = (type_, default_value, optional, enum)
                        filename = info['filename']
                        self.file2wrap[filename] = self.file2wrap.get(filename, []) + [{d: {'attr': attr,
                                                         'view_name': component._view_name.default_value,
                                                         'model_name': component._model_name.default_value, 
                                                         'base': [get_class_info(self.module, base) for base in component.__bases__]
                                                   }}]

    def build_output(self, traits2lang):
        self.output = []
        class2file = {}
        for filename, classes in self.file2wrap.items():
            for cl in classes:
                for classname in cl.keys():
                    class2file[classname] = filename.split('/')[-1]

        for filename, classes in self.file2wrap.items():
            klass = {}
            dependencies = set()
            for cl in classes:
                for classname, classdata in cl.items():
                    tmp = OrderedDict()
                    ltmp = []
                    using = []
                    for varname, vardata in classdata['attr'].items():
                        unknown = False
                        if isinstance(vardata[0], tuple):
                            container = get_trait(vardata[0][0], traits2lang, class2file)
                            if container is None:
                                print("unknown container type for {} in class {}".format(varname, classname))
                                unknown = True
                            element = get_trait(vardata[0][1], traits2lang, class2file)
                            if element is None:
                                print("unknown element type for the container {} in class {}".format(varname, classname))
                                unknown = True
                            cpptype = container + '<' + element + '>'

                            for v in vardata[0]:
                                dep = get_dep(v, traits2lang, class2file)
                                if dep and dep != filename +'.hpp':
                                    dependencies.update({dep}) 

                                to_add = get_using(v, traits2lang)
                                if to_add and to_add not in using:
                                    using.append(to_add)
                        else:
                            cpptype = get_trait(vardata[0], traits2lang, class2file)
                            if cpptype is None:
                                print("unknown type for {} in class {}".format(varname, classname))
                                unknown = True

                            dep = get_dep(vardata[0], traits2lang, class2file)
                            if dep and dep != filename + '.hpp':
                                dependencies.update({dep})

                            to_add = get_using(vardata[0], traits2lang)

                            if to_add and to_add not in using:
                                using.append(to_add)
                        if vardata[3]:
                            cpptype = "X_CASELESS_STR_ENUM("+', '.join([e for e in vardata[3]])+')'
                        
                        default_value = vardata[1]
                        ltmp.append({'name': varname, 'type': cpptype, 'default_value': default_value, 'optional': vardata[2], 'comment': '//' if unknown else ''})

                    tmp['attr'] = ltmp
                    tmp['using'] = using
                    tmp['view_name'] = classdata['view_name']
                    tmp['model_name'] = classdata['model_name']
                    for i in classdata['base']:
                        if i['classname'] in class2file.keys():
                            tmp['inheritance'] = [python2cpp_classname(i['classname'], 'x')]
                        else:
                            dependencies.update({i['filename']})
                            tmp['inheritance'] = [python2cpp_classname(i['classname']) for i in classdata['base']]
                    #dependencies = dependencies.union(set([i['filename'] for i in classdata['base']]))
                    cppclassname = python2cpp_classname(classname, 'x')
                    klass[cppclassname] = tmp
            # remove the dependency of the same file
            dependencies = sorted(dependencies - {filename+self.prefix})
            self.output.append((filename, dependencies, klass))
        
    def build_files(self, template, path='output', prefix='.hpp'):
        from jinja2 import Environment, PackageLoader, select_autoescape
        env = Environment(
            loader=PackageLoader('wrapper', 'templates'),
            autoescape=select_autoescape(['tmpl']),
            trim_blocks=False,
            lstrip_blocks=True
        )
        template = env.get_template(template)

        for r in self.output:
            filename, dependencies, class2wrap = r
            output_file = path + '/' + self.module + '/' + filename + prefix
            print(self.module,  output_file)
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
            with open(output_file, mode='w') as f:
                f.write(template.render(namespace=self.namespace, 
                                        package_name=self.package_name.upper(),
                                        filename=filename.upper(),
                                        dependencies=dependencies, 
                                        klass=klass))

w = wrapper('pythreejs', 'xthree', 'xthree')
#w = wrapper('bqplot', 'xpl', 'xplot')
w.build_files('cpp.tmpl')
