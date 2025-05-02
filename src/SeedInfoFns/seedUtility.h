/**
 * Utilities for conditions that can't be checked on the frontend(lapis.py)
 * Since commands are called as !nearest <biome or stronghold>
 * the C portion needs to check what the type of the parameter is
*/
enum BiomeID get_biome_id(const char *biome);
enum StructureType get_structure_id(const char* structure);
Pos findNearestStructure(enum StructureType sType, int blockX, int blockZ, int maxRadius);
Pos nearestBiome(char *biome, int xCoord, int yCoord, int zCoord, int range, enum BiomeID bID);
uint64_t generate_random_seed(uint64_t range_limit);

typedef struct {
    const char *name;
    enum BiomeID id;
} BiomeLookup;
#define BIOME_ENTRY(name) {#name, name}

typedef struct {
    const char *name;
    enum StructureType id;
} StructureLookup;
#define STRUCTURE_ENTRY(name) {#name, name}

// data for an individual seed
typedef struct {
    uint64_t seed;
    Pos spawnCoordinates;
} SeedEntry;


/**
 * list of all found seeds, and the list length
*/
typedef struct {
    const int length;
    SeedEntry* seeds;
} SeedArray;

