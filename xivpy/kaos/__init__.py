from typing     import TYPE_CHECKING
  
from .data      import get_definitions
from .tagfile   import Node
from .tagfile   import Tagfile
from .tagfile   import Definition
from .animation import QuantisedAnimation, create_raw_tracks

if TYPE_CHECKING:
    from .nodes  import *
