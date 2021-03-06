traits2cpp = {
 #'All',
 #'Any',
 'Array': {'type': 'data_type', 'using': 'xboxed_container<std::vector<double>>'},
 #'BaseDescriptor',
 'Bool': 'bool',
 #'Bunch',
 #'Bytes',
 'CBool': 'bool',
 #'CBytes',
 'CComplex': 'std::complex',
 'CFloat': 'double',
 'CInt': 'int',
 'CLong': 'std::size_t',
 #'CRegExp',
 #'CUnicode': cppstring,
 #'CaselessStrEnum',
 #'ClassBasedTraitType',
 #'ClassTypes',
 'Complex': 'std::complex',
 #'Container',
 #'DefaultHandler',
 'Dict': '::xeus::xjson',
 #'DottedObjectName',
 'Enum': 'enum',
 #'EventHandler',
 'Float': 'double',
 #'ForwardDeclaredInstance',
 #'ForwardDeclaredMixin',
 #'ForwardDeclaredType',
 #'HasDescriptors',
 #'HasTraits',
 #'Instance',
 'Int': 'int',
 'Integer': 'int',
 'List': {'type': 'std::vector', 'include': 'vector'},
 'Long': 'std::size_t',
 #'MetaHasDescriptors',
 #'MetaHasTraits',
 #'NoDefaultSpecified',
 #'ObjectName',
 #'ObserveHandler',
 #'Sentinel',
 #'SequenceTypes',
 'Set': 'std::set',
 #'TCPAddress',
 #'This',
 #'TraitError',
 #'TraitType',
 'Tuple': {'type':'pair_type', 'using': 'std::pair<double, double>'},
 #'Type',
 #'Undefined',
 'Unicode': {'type': 'std::string', 'include': 'string'},
 'Union': 'union',
 #'UseEnum',
 #'ValidateHandler',
 # bqplot type
 'Color': {'type': 'color_type', 'using': 'std::string'},
}

classLink = {
    "Widget": {'filename': "xplot.hpp", 'classname': "xplot"},
    "DOMWidget": {'filename': "xwidgets/xwidget.hpp", 'classname': "xw::xwidget"}, 
}