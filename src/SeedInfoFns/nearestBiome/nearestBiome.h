#include "../../../external/cubiomes/finders.h"
/**
 * Find the nearest chosen biome closest to the given coordinates within some range.
 * When users interacting with the bot call this service, they won't directly pass the bot
 * every field.
*/
Pos nearestBiome(char *biome, int xCoord, int yCoord, int zCoord, int range, enum BiomeID bID, Generator bg);