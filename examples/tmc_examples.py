from iocbuilder import Substitution
from iocbuilder.arginfo import *


class ex1(Substitution):
    '''This is a simple template wrapper with no defaults'''

    # __init__ attributes
    # This tells the gui the type and description of each argument
    # In this case we have no __init__ method, so the arguments passed
    # to ArgInfo are our only argument source
    ArgInfo = makeArgInfo(
        # The Simple function tells the gui this is a simple str
        arg1 = Simple('Argument 1 description', str),
        # or a simple int
        arg2 = Simple('Argument 2 description', int))

    # Substitution attributes 
    # This specifies the template file. It must exist in the db directory of
    # the current module
    TemplateFile = 'ex1.template'        
    # This specifies the list of arguments that must exist for this template
    Arguments = ['arg1', 'arg2']


class ex2(Substitution):
    '''This is a template wrapper with defaults'''

    # The __init__ method specifies arguments and defaults
    def __init__(self, arg1, arg2 = 42):        
        # Use the __super attribute to initialise ensures the superclasses
        # are initialised in the correct order.        
        self.__super.__init__(arg1 = arg1, arg2 = arg2)

    # __init__ attributes                        
    # This time we take the argument info from the __init__ method
    # This ensures we pick up the defaults
    ArgInfo = makeArgInfo(__init__,
        arg1 = Simple('Argument 1 description', str),
        arg2 = Simple('Argument 2 description', int))

    # Substitution attributes    
    TemplateFile = 'ex2.template'       
    # This time we can generate Arguments from ArgInfo     
    Arguments = ArgInfo.Names()



class ex3(Substitution):
    '''This is a more complicated template wrapper with defaults'''

    # The __init__ method specifies arguments and defaults
    def __init__(self, arg1, arg2 = 1.0, arg3 = True, arg4 = 2):
        # This time we have lots more arguments, so it is easier to        
        # take the dict of local variables and filter it by self.Arguments
        args = filter_dict(locals(), self.Arguments)
        # The ** operator unpacks the dict as named arguments to pass to
        # the Substitution subclass      
        self.__super.__init__(**args)

    # __init__ attributes            
    ArgInfo = makeArgInfo(__init__,
        # The Simple function can take a str
        arg1 = Simple('Argument 1 description', str),
        # or a float
        arg2 = Simple('Argument 2 description', float),
        # or a bool
        arg3 = Simple('Argument 3 description', bool),
        # or an int
        arg4 = Simple('Argument 4 description', int))
        
    # Substitution attributes    
    TemplateFile = 'ex3.template'        
    Arguments = ArgInfo.Names()

    
class ex4(Substitution):
    '''This is a template wrapper that takes some arguments from a parent
    object and uses them in the template'''
    
    # Do some aggregation of arguments from the parent object
    def __init__(self, parent, arg3 = "b", arg4 = 0, arg5 = "MINOR"):
        # extract arg1 and arg2 from the parent object
        arg1 = parent.args["arg1"]
        arg2 = parent.args["arg2"]
        # pass the relevant arguments to the super intialiser
        self.__super.__init__(**filter_dict(locals(), self.Arguments))
        
    # __init__ attributes            
    ArgInfo = makeArgInfo(__init__,
        # The Ident function will only allow us to choose objects that are
        # instances of ex3 in the gui
        parent = Ident ('Parent Object', ex3),
        # The Choice function gives a selection of one of the list
        arg3   = Choice('Argument 3 description', ["a", "b", "c"]),        
        # The Enum function displays a choice, but stores the index of the list
        arg4   = Enum  ('Argument 4 description', ["ZERO", "ONE", "TWO"]),             
        # The Sevr function is just a choice of epics severities
        arg5   = Sevr  ('Argument 5 description'))

    # Substitution attributes                
    TemplateFile = 'ex3.template'        
    # The excludes keyword allows us to exclude a particular keyword from
    # the list of Names returned from ArgInfo
    Arguments = ["arg1", "arg2"] + ArgInfo.Names(without = ["parent"])
    

class ex5(Substitution, AutoProtocol):
    '''This is a template that uses streamdevice'''

    # __init__ attributes
    ArgInfo = makeArgInfo(
        device = Simple('Device Prefix', str),
        port   = Ident ('Asyn Serial Port', AsynOctetInterface))
        
    # Substitution attributes
    TemplateFile = 'ex5.template'        
    Arguments = ArgInfo.Names()
    
    # AutoProtocol attributes
    # This is the list of protocol files streamdevice needs to know about
    ProtocolFiles = ['ex5.proto']
    
