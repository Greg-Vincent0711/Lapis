#include <stdio.h>
#include "limits.h"
#include "../../../external/cubiomes/finders.h"
/**
 * Find the nearest chosen structure closest to the given coordinates within some range.
 * When users interacting with the bot call this service, they won't directly pass the bot
 * every field.
*/
Pos findNearestStructure(enum StructureType sType, int blockX, int blockZ, int maxRadius, Generator bg);