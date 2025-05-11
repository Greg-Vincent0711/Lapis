#include "../../../external/cubiomes/finders.h"
#include "../utilityFns/utilityFns.h"
/**
 * Return seeds with certain spawn conditions. User will not directly pass the bot every single field.
*/
SeedArray spawnNear(int numSeeds, char* biome, char* structure, int radiusFromSpawn, Generator biomeGenerator);