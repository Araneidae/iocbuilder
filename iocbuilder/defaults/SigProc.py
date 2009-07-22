from iocbuilder import Substitution, Device
from iocbuilder.arginfo import *

DTYPS = ( "FFT",
          "FFT Hann",
          "FFT Hamming",
          "FFT Blackman",
          "FFT Blackman-Harris",
          "FFT Kaiser-Bessel",
          "FFT Gauss" )

class fftWaveform(Substitution, Device):
    '''Create a waveform record that displays the fourier transform of its
    input'''

    # just pass the args straight through
    def __init__(self,
            P, INP, name = '', DTYP = "FFT", NELM = 25000, RARM = 0): 
        self.__super.__init__(**filter_dict(locals(), self.Arguments))

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        P    = Simple('Device Prefix', str),
        INP  = Simple('Input waveform for fft', str),
        DTYP = Choice('FFT type', DTYPS),
        NELM = Simple('Number of elements, should be half the size of the input waveform', int),
        RARM = Simple('Set this to the window number if using windowing', int),
        name = Simple('Object name', str))

    # Substitution attributes
    Arguments = ArgInfo.Names()
    TemplateFile = 'fftWaveform.template'        
        
    # Device attributes
    DbdFileList = ['fft', 'Window']
    LibFileList = ['fft', 'Window']
    
