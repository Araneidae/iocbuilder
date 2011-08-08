'''Support for default record name configurations.'''

import string

__all__ = [
    'BasicRecordNames', 'TemplateRecordNames', 'DiamondRecordNames',
    'RecordName']


# Base class for record name configuration.
class RecordNamesBase:
    def RecordName(self, name):
        return name


## Default record name support: each record is created with precisely the name
# it is given.
class BasicRecordNames(RecordNamesBase):

    __VersionInfo = { '3.13' : 29, '3.14' : 61 }

    # The version parameter specifies the EPICS version: this determines
    # the maximum name length.
    def __init__(self, version='3.14'):
        self.maxLength = self.__VersionInfo[version]

    def RecordName(self, name):
        assert 0 < len(name) <= self.maxLength, \
            'Record name "%s" too long' % name
        return name


## Simple support for building templates.
#
# Records are named "$(DEVICE):name".
class TemplateRecordNames(RecordNamesBase):
    __all__ = ['TemplateName', 'Parameter']

    ## A Parameter is used to wrap a template parameter before being assigned to
    # a record field.
    class Parameter:
        __ParameterNames = set()

        def __init__(self, name, description = '', default = None):
            # Ensure names aren't accidentially removed
            assert name not in self.__ParameterNames, \
                'Parameter name "%s" already defined' % name
            self.__ParameterNames.add(name)

            self.__name = name
            self.__default = default

            # Add the description as metadata to the current record set
            from recordset import RecordSet
            lines = description.split('\n')
            RecordSet.AddHeaderLine('#%% macro, %s, %s' % (name, lines[0]))
            for line in lines[1:]:
                RecordSet.AddHeaderLine('#  %s' % line)

        def __str__(self):
            if self.__default is None:
                return '$(%s)' % self.__name
            else:
                return '$(%s=%s)' % (self.__name, self.__default)

        def Validate(self, record, field):
            return True


    def __init__(self, device=None):
        if device is None:
            device = self.Parameter('DEVICE', 'Device name')
        self.__Name = device

    def RecordName(self, name):
        return '%s:%s' % (self.__Name, name)

    ## Can be used to update the template name.
    def TemplateName(self, name):
        self.__Name = name


## Support for record names following the Diamond naming convention.
# Record names are of the form
# \code
#     DD[DDD]-TT-CCCCC-NN:RRRRRRRRRR
# \endcode
# where \c DDDDD names a domain within the machine, \c TT names a technical
# area, \c CCCCC names a device (or component), \c NN is a two digit sequence
# number, and \c RRRRRRRRRR is the final part of the record name.
#
# When this naming convention is enabled the domain, technical area,
# device and sequence number (id) are specified before records are
# created using the methods SetDomain, SetTechnicalArea and SetDevice.
# When each record is created only the final part of its name then needs
# to be specified.
class DiamondRecordNames(RecordNamesBase):
    __all__ = [
        'SetDomain', 'SetTechnicalArea', 'SetDevice', 'GetDevice',
        'UnsetDevice']

    # The allowable characters in a record name are defined here: [A-Z0-9_-]
    ValidRecordNameChars = set(string.ascii_uppercase + string.digits + '_-')

    __VersionInfo = { '3.13' : (10, 2), '3.14' : (42, 20) }

    # The version parameter identifies the epics version.  This determines
    # the maximum name length and other naming conventions.
    def __init__(self, version='3.14'):
        self.__MaxNameLength, self.__MaxNameComponents = \
            self.__VersionInfo[version]
        self.__TechnicalArea = None
        self.__Domain = None
        self.__Device = None

    ## The domain, and optionally the technical area, are set by calling this
    # routine.  Both of these must be defined before records can be created.
    #
    # \param domain
    #   The machine domain for records to be created.  Frequently this only
    #   needs to be set once, as an IOC will only serve records for one
    #   machine domain.
    # \param area
    #   The technical area used for records being created.  This can be
    #   omitted, in which case SetTechnicalArea() must be called.
    def SetDomain(self, domain, area=None):
        assert 0 < len(domain) <= 5, 'Invalid domain name %s' % domain
        # Set the technical area and domain
        self.__Domain = domain
        if area:
            self.SetTechnicalArea(area)


    ## Sets the technical area for record creation.  Only required if
    # SetDomain() was called with only one parameter.
    def SetTechnicalArea(self, area):
        assert len(area) == 2, 'Invalid area name %s' % area
        self.__TechnicalArea = area


    ## Sets the component and its id before records are created.
    # This function must be called before creating any records.  By default
    # it takes just the component and id parameters, but the entire device
    # name can be specified if required.
    #
    # Note that normally SetDomain() should be called first, but domain and
    # area can be specified if appropriate.
    #
    # \param component
    #   The component name for records.
    # \param id
    #   The component identifier number.  Must be a number in the range 1 to
    #   99.
    # \param domain
    #   The domain can be overridden here.
    # \param area
    #   Similarly the technical area can be overridden.
    def SetDevice(self, component, id, domain=None, area=None):
        if domain is not None:
            self.__Domain = domain
        if area is not None:
            self.__TechnicalArea = area
        assert self.__TechnicalArea != None and self.__Domain != None, \
            'Must set domain and area before creating records'
        assert 0 < len(component) <= 5, 'Invalid component name %s' % component
        assert 0 < id  and id <= 99, 'Invalid id number %d' % id
        self.__Device = '%s-%s-%s-%02d' % (
            self.__Domain, self.__TechnicalArea, component, id)


    ## Returns the currently set device name.
    def GetDevice(self):
        if self.__Device:
            return self.__Device
        else:
            raise AttributeError('Device not currently defined')


    ## This should be called after creating a block of records to ensure that
    # the device name isn't incorrectly reused.'  SetDevice() must be called
    # again before further records are created.
    def UnsetDevice(self):
        self.__Device = None



    # Computes a record name.  Under version 3.13 rules a valid record name
    # is no more than 10 characters and consists of one or two components
    # separated by a ':' where each component can only contain upper case
    # letters, digits or underscores.  The rules for 3.14 allow for longer
    # names with more components.
    def RecordName(self, record, device=None):
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

        assert device is not None, 'Must define device name first'
        return '%s:%s' % (device, record)



# By default we use an instance of RecordNamesBase for record names, but this
# can be rebound during configuration.
RecordNames = RecordNamesBase()
def RecordName(*args, **kargs):
    return RecordNames.RecordName(*args, **kargs)
