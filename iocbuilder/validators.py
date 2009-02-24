'''Some common validator functions.'''

def TwoDigitInt(i):
    return '%02i' % int(i)

def asynPort(p):
    return p.DeviceName()

def strOrNone(x):
    if x is None:
        return x
    else:
        return str(x)
        
def intOrNone(x):
    if x is None:
        return x
    else:
        return int(x)        
