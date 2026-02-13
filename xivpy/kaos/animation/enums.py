from enum import Enum

class AnimationType(Enum): 
    UNKNOWN     = 0,
    INTERLEAVED = 1,
    SPLIE       = 3,
    QUANTIZED   = 4,
    PREDICTIVE  = 5,

class Space(Enum): 
    NATIVE  = "NATIVE",
    BLENDER = "BLENDER",

