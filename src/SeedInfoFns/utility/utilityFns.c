#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include <limits.h>
#include "../../external/cubiomes/biomes.h"
#include "../../external/cubiomes/finders.h"
#include "utilityFns.h"

// will add support for Nether and End in the future

StructureLookup structure_map[] = {
    STRUCTURE_ENTRY(Desert_Pyramid),
    STRUCTURE_ENTRY(Jungle_Temple),
    STRUCTURE_ENTRY(Jungle_Pyramid) ,
    STRUCTURE_ENTRY(Swamp_Hut),
    STRUCTURE_ENTRY(Igloo),
    STRUCTURE_ENTRY(Village),
    STRUCTURE_ENTRY(Ocean_Ruin),
    STRUCTURE_ENTRY(Shipwreck),
    STRUCTURE_ENTRY(Monument),
    STRUCTURE_ENTRY(Mansion),
    STRUCTURE_ENTRY(Outpost),
    STRUCTURE_ENTRY(Ruined_Portal),
    STRUCTURE_ENTRY(Ruined_Portal_N),
    STRUCTURE_ENTRY(Ancient_City),
    STRUCTURE_ENTRY(Treasure),
    STRUCTURE_ENTRY(Mineshaft),
    STRUCTURE_ENTRY(Desert_Well),
    STRUCTURE_ENTRY(Geode),
    // STRUCTURE_ENTRY(Fortress),
    // STRUCTURE_ENTRY(Bastion),
    // STRUCTURE_ENTRY(End_City),
    // STRUCTURE_ENTRY(End_Gateway),
    // STRUCTURE_ENTRY(End_Island),
    STRUCTURE_ENTRY(Trail_Ruins),
    STRUCTURE_ENTRY(Trial_Chambers),
};

int NUM_STRUCTURES = sizeof(structure_map) / sizeof(structure_map[0]);
enum StructureType get_structure_id(const char *structure) {
    for (int entry = 0; entry < NUM_STRUCTURES; entry++) {
        if (strcmp(structure, structure_map[entry].name) == 0) {
            return structure_map[entry].id;
        }
    }
    return -INT_MAX;
}

BiomeLookup biome_map[] = {
    BIOME_ENTRY(ocean), 
    BIOME_ENTRY(plains),
    BIOME_ENTRY(desert),
    BIOME_ENTRY(mountains),
    BIOME_ENTRY(extremeHills),
    BIOME_ENTRY(forest), 
    BIOME_ENTRY(taiga),
    BIOME_ENTRY(swamp), 
    BIOME_ENTRY(swampland),
    BIOME_ENTRY(river),
    // BIOME_ENTRY(nether_wastes),
    // BIOME_ENTRY(hell), 
    // BIOME_ENTRY(the_end),
    BIOME_ENTRY(frozen_ocean),
    BIOME_ENTRY(frozen_river),
    BIOME_ENTRY(snowy_tundra),
    BIOME_ENTRY(snowy_mountains),
    BIOME_ENTRY(mushroom_fields),
    BIOME_ENTRY(mushroom_field_shore), 
    BIOME_ENTRY(beach),
    BIOME_ENTRY(desert_hills), 
    BIOME_ENTRY(wooded_hills), 
    BIOME_ENTRY(taiga_hills),
    BIOME_ENTRY(mountain_edge),
    BIOME_ENTRY(jungle),
    BIOME_ENTRY(jungle_hills),
    BIOME_ENTRY(jungle_edge),
    BIOME_ENTRY(deep_ocean),
    BIOME_ENTRY(stone_shore),
    BIOME_ENTRY(snowy_beach),
    BIOME_ENTRY(birch_forest),
    BIOME_ENTRY(birch_forest_hills),
    BIOME_ENTRY(dark_forest),
    BIOME_ENTRY(snowy_taiga),
    BIOME_ENTRY(snowy_taiga_hills),
    BIOME_ENTRY(giant_tree_taiga),
    BIOME_ENTRY(giant_tree_taiga_hills),
    BIOME_ENTRY(wooded_mountains),
    BIOME_ENTRY(savanna),
    BIOME_ENTRY(savanna_plateau),
    BIOME_ENTRY(badlands),
    BIOME_ENTRY(wooded_badlands_plateau),
    BIOME_ENTRY(badlands_plateau),
    BIOME_ENTRY(small_end_islands),
    BIOME_ENTRY(end_midlands),
    BIOME_ENTRY(end_highlands),
    BIOME_ENTRY(end_barrens),
    BIOME_ENTRY(warm_ocean),
    BIOME_ENTRY(lukewarm_ocean),
    BIOME_ENTRY(cold_ocean),
    BIOME_ENTRY(deep_warm_ocean),
    BIOME_ENTRY(deep_lukewarm_ocean),
    BIOME_ENTRY(deep_cold_ocean),
    BIOME_ENTRY(deep_frozen_ocean),
    BIOME_ENTRY(seasonal_forest),
    BIOME_ENTRY(rainforest),
    BIOME_ENTRY(shrubland),
    // IDS greater than 64 below
    // BIOME_ENTRY(the_void),
    BIOME_ENTRY(sunflower_plains),
    BIOME_ENTRY(desert_lakes),
    BIOME_ENTRY(gravelly_mountains),
    BIOME_ENTRY(flower_forest),
    BIOME_ENTRY(taiga_mountains),
    BIOME_ENTRY(swamp_hills),
    BIOME_ENTRY(ice_spikes),
    BIOME_ENTRY(modified_jungle),
    BIOME_ENTRY(modified_jungle_edge),
    BIOME_ENTRY(tall_birch_forest),
    BIOME_ENTRY(tall_birch_hills),
    BIOME_ENTRY(dark_forest_hills),
    BIOME_ENTRY(snowy_taiga_mountains),
    BIOME_ENTRY(giant_spruce_taiga),
    BIOME_ENTRY(giant_spruce_taiga_hills),
    BIOME_ENTRY(modified_gravelly_mountains),
    BIOME_ENTRY(shattered_savanna),
    BIOME_ENTRY(shattered_savanna_plateau),
    BIOME_ENTRY(eroded_badlands),
    BIOME_ENTRY(modified_wooded_badlands_plateau),
    BIOME_ENTRY(modified_badlands_plateau),
    BIOME_ENTRY(bamboo_jungle),
    BIOME_ENTRY(bamboo_jungle_hills),
    // BIOME_ENTRY(soul_sand_valley),
    // BIOME_ENTRY(crimson_forest),
    // BIOME_ENTRY(warped_forest),
    // BIOME_ENTRY(basalt_deltas),
    BIOME_ENTRY(dripstone_caves),
    BIOME_ENTRY(lush_caves),
    BIOME_ENTRY(meadow),
    BIOME_ENTRY(grove),
    BIOME_ENTRY(snowy_slopes),
    BIOME_ENTRY(jagged_peaks),
    BIOME_ENTRY(frozen_peaks),
    BIOME_ENTRY(stony_peaks),
    BIOME_ENTRY(deep_dark),
    BIOME_ENTRY(mangrove_swamp),
    BIOME_ENTRY(cherry_grove),
    BIOME_ENTRY(pale_garden),
}; 
int NUM_BIOMES = sizeof(biome_map) / sizeof(biome_map[0]);

enum BiomeID get_biome_id(const char *biome) {
    for (int entry = 0; entry < NUM_BIOMES; entry++) {
        if (strcmp(biome, biome_map[entry].name) == 0) {
            return biome_map[entry].id;
        }
    }
    return -INT_MAX;
}

uint64_t generate_random_seed(uint64_t range_limit) {
    srand(time(NULL));
    long mask = 0x7FFFFFFFFFFFFFFF;
    // ensure we take only the lowest 16 bits
    int clamp = 0xFFFF;
    /**
     * create a 64-bit random integer
     * rand() returns 15 bits at a time
     * << 48 moves 16 bits into highest section of 64 bit seed
     * << 32 moves 16 bits into next highest section
    */
    uint64_t high = ((uint64_t)rand() & clamp) << 48;
    uint64_t mid = ((uint64_t)rand() & clamp) << 32;
    // low is a full 32 bit integer
    uint64_t low = ((uint64_t)rand() << 16) | (rand() & clamp);
    // put all the different integers together, mask them within MC seed range
    uint64_t random_seed = (high | mid | low) & mask;

    if (random_seed > UINT64_MAX - range_limit) {
        random_seed = UINT64_MAX - range_limit;
    }

    return random_seed;
}