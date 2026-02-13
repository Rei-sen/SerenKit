from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import hkRootLevelContainerNode, hkRootLevelContainerNamedVariantNode
    from .anim import (hkaAnimationContainerNode, hkaSkeletonNode, hkaBoneNode, 
                       hkaSkeletonMapperNode, hkaSkeletonMapperDataNode, 
                       hkaSkeletonMapperDataSimpleMappingNode, hkaAnimationBindingNode,
                       hkaAnimationNode, hkaInterleavedUncompressedAnimationNode, hkaQuantizedAnimationNode,
                       hkaSplineCompressedAnimationNode)
