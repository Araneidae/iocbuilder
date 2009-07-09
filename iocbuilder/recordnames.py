# Support for default record name configurations.

import string

__all__ = ['BasicRecordNames', 'TemplateRecordNames', 'DiamondRecordNames']


class RecordNamesBase:
    '''Base class for record name configuration.'''
    def RecordName(self, name):
        return name


class BasicRecordNames(RecordNamesBase):
    '''Default record name support: each record is created with precisely
    the name it is given.'''

    __VersionInfo = { '3.13' : 29, '3.14' : 61 }
    
    def __init__(self, version='3.14'):
        '''The version parameter specifies the EPICS version: this determines
        the maximum name length.'''
        self.maxLength = self.__VersionInfo[version]

    def RecordName(self, name):
        '''Internal method.'''
        assert 0 < len(name) <= self.maxLength, \
            'Record name "%s" too long' % name
        return name


class TemplateRecordNames(RecordNamesBase):
    '''Simple support for building templates.  To be expanded.'''
    
    __all__ = ['TemplateName']
 
    def __init__(self, device='DEVICE'):
        self.__Name = device
        
    def RecordName(self, name):
        '''Internal method.'''
        return '$(%s):%s' % (self.__Name, name)

    def TemplateName(self, name):
        '''Sets the template name (default value is 'DEVICE').'''
        self.__Name = name
    

class DiamondRecordNames(RecordNamesBase):
    '''Support for record names following the Diamond naming convention.
    Record names are of the form
        DD[DDD]-TT-CCCCC-NN:RRRRRRRRRR
    where DDDDD names a domain within the machine, TT names a technical
    area, CCCCC names a device (or component), NN is a two digit sequence
    number, and RRRRRRRRRR is the final part of the record name.

    When this naming convention is enabled the domain, technical area,
    device and sequence number (id) are specified before records are
    created using the methods SetDomain, SetTechnicalArea and SetDevice.
    When each record is created only the final part of its name then needs
    to be specified.'''
    
    __all__ = [
        'SetDomain', 'SetTechnicalArea', 'SetDevice', 'GetDevice',
        'UnsetDevice', 'RecordName' ]

    # The allowable characters in a record name are defined here: [A-Z0-9_-]
    ValidRecordNameChars = set(string.ascii_uppercase + string.digits + '_-')

    __VersionInfo = { '3.13' : (10, 2), '3.14' : (42, 20) }

    def __init__(self, version='3.13'):
        '''The version parameter identifies the epics version.  This determines
        the maximum name length and other naming conventions.'''
        self.__MaxNameLength, self.__MaxNameComponents = \
            self.__VersionInfo[version]
        self.__TechnicalArea = None
        self.__Domain = None
        self.__Device = None

    def SetDomain(self, domain, area=None):
        '''The domain, and optionally the technical area, are set by calling
        this routine.  Both of these must be defined before records can be
        created.'''
        assert 0 < len(domain) <= 5, 'Invalid domain name %s' % domain
        # Set the technical area and domain
        self.__Domain = domain
        if area:
            self.SetTechnicalArea(area)


    def SetTechnicalArea(self, area):
        '''Sets the technical area for record creation.'''
        assert len(area) == 2, 'Invalid area name %s' % area
        self.__TechnicalArea = area


    def SetDevice(self, component, id, domain=None, ta=None):
        '''Sets the component and its id before records are created.'''
        if domain is not None:
            self.__Domain = domain
        if ta is not None:
            self.__TechnicalArea = ta
        assert self.__TechnicalArea != None and self.__Domain != None, \
            'Must set domain and area before creating records'
        assert 0 < len(component) <= 5, 'Invalid component name %s' % component
        assert 0 < id  and id <= 99, 'Invalid id number %d' % id
        self.__Device = '%s-%s-%s-%02d' % (
            self.__Domain, self.__TechnicalArea, component, id)


    def GetDevice(self):
        '''Returns the currently set device name.'''
        if self.__Device:
            return self.__Device
        else:
            raise AttributeError('Device not currently defined')


    def UnsetDevice(self):
        '''This should be called after creating a block of records to ensure
        that the device name isn't incorrectly reused.'  SetDevice() must be
        called again before further records are created.'''
        self.__Device = None



    # Computes a record name.  Under version 3.13 rules a valid record name
    # is no more than 10 characters and consists of one or two components
    # separated by a ':' where each component can only contain upper case
    # letters, digits or underscores.  The rules for 3.14 allow for longer
    # names with more components.
    def RecordName(self, record, device=None):
        '''Internal method.'''
        if not device:  device = self.__Device
        assert 0 < len(record) <= self.__MaxNameLength, \
               'Record name "%s" too long' % record
        # Validate the record name components
        componentList = record.split(':')
        assert len(componentList) <= self.__MaxNameComponents, \
               'No more than two device components allowed in name "%s"' \
               % record
        for component in componentList:
            assert len(component) > 0, \
                   'Empty component in name "%s" not allowed' % record
            assert set(component) <= self.ValidRecordNameChars, \
                   'Invalid character(s) in record name "%s"' % record

        assert device != None, 'Must define device name first'
        return '%s:%s' % (device, record)



# By default we use an instance of RecordNamesBase for record names, but this
# can be rebound during configuration.
RecordNames = RecordNamesBase()