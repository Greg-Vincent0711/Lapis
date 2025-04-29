/**
 * Utilities for conditions that can't be checked on the frontend(lapis.py)
 * Since commands are called as !nearest <biome or stronghold>
 * the C portion needs to check what the type of the parameter is
*/
enum BiomeID get_biome_id(const char *biome);
enum StructureType get_structure_id(const char* structure);
Pos findNearestStructure(enum StructureType sType, int blockX, int blockZ, int maxRadius);
Pos nearestBiome(char *biome, int xCoord, int yCoord, int zCoord, int range, enum BiomeID bID);