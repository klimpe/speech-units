cdef extern from "stdio.h":
    cdef extern void printf(...)

cdef extern from "flite.h":

    cdef struct cst_voice:
        pass

    cdef extern void flite_init()
    cdef extern cst_voice *register_cmu_us_kal()
    cdef extern void  unregister_cmu_us_kal(cst_voice *voice)
    cdef extern float flite_text_to_speech(char *text, cst_voice *voice, char *outtype)
    cdef extern float flite_file_to_speech(char *fileName, cst_voice *voice, char *outtype)


cdef float say_imp( char *text, char *fileName):
    cdef cst_voice *voice
    voice = register_cmu_us_kal()
    seconds = flite_text_to_speech( text, voice, fileName)
    unregister_cmu_us_kal(voice)
    return seconds

cdef float sayFile_imp( char *srcFileName, char *fileName):
    cdef cst_voice *voice
    voice = register_cmu_us_kal()
    seconds = flite_file_to_speech( srcFileName, voice, fileName)
    unregister_cmu_us_kal(voice)
    return seconds

    


def init():
    """This must be called before any other flite function can be called."""
    flite_init()

def say( text, fileName="play" ):
    """ say( text [, fileName]): text = text to speak, if fileName is given, writes wav output to that file, returns number of seconds of speech generated """
    return say_imp(text, fileName)

def sayFile( srcFileName, fileName="play" ):
    """ sayFile( srcFileName [, fileName]): srcFileName = file to speak, if fileName is given, writes wav output to that file, returns number of seconds of speech generated """
    return sayFile_imp(srcFileName, fileName)
 
    
