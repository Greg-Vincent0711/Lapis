#include <stdio.h>
#include "limits.h"
#include "../../../external/cubiomes/finders.h"

Pos findNearestStructure(enum StructureType sType, int blockX, int blockZ, int maxRadius, Generator bg);