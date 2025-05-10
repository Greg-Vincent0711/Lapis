#include "stdio.h"
#include "../../../external/cubiomes/finders.h"
#include "limits.h"
#include "../utility/utilityFns.h"
#include "../nearestStructure/nearestStructure.h"

/**
 * Returns a seed or multiple with the specified spawn conditions
 * Read parameters as: x seeds where I spawn in this biome, with a structure x blocks from spawn
*/
SeedArray spawnNear(int numSeeds, char* biome, char* structure, int radiusFromSpawn, Generator biomeGenerator) {
    // max params are subject to change
    const int MAX_RADIUS = 3000;
    const int MAX_SEEDS = 10;
    if (numSeeds <= 0 || numSeeds > MAX_SEEDS) {
        fprintf(stderr, "Invalid number of seeds requested. Must be greater than 0 and no greater than %d.\n", MAX_SEEDS);
        return (SeedArray){ .seeds = NULL, .length = 0 };
    }

    int bID = biome != 'None' ? get_biome_id(biome) : -INT_MAX;
    int sID = structure != 'None' ? get_structure_id(structure) : -INT_MAX;
    
    if (bID == -INT_MAX && sID == -INT_MAX) {
        fprintf(stderr, "Check your spelling. You must provide either a biome or structure as a search parameter.\n");
        return (SeedArray){ .seeds = NULL, .length = 0 };
    }

    if (radiusFromSpawn <= 0 || radiusFromSpawn > MAX_RADIUS) {
        fprintf(stderr, "Invalid radius. Must be greater than 0 and no greater than %d.\n", MAX_RADIUS);
        return (SeedArray){ .seeds = NULL, .length = 0 };
    }

    SeedEntry* foundSeeds = malloc(sizeof(SeedEntry) * numSeeds);
    if (!foundSeeds) {
        fprintf(stderr, "Memory allocation failed\n");
        return (SeedArray){ .seeds = NULL, .length = 0 };
    }

    int amountFound = 0;
    /**
     * In future versions, add ability to change how many seeds can be searched
     * For free version, 1,000,000 is fine
     * TODO - add support for end and nether in future versions
     * getSpawn fn is not 100% accurate
    */
    int seedSearchLimit = 1000000;
    uint64_t seedStart = generate_random_seed(seedSearchLimit);
    for (uint64_t seed = seedStart; seed < seedStart + seedSearchLimit; seed++) {
        applySeed(&biomeGenerator, biomeGenerator.dim, seed);
        Pos spawn = getSpawn(&biomeGenerator);
        // MC coords(X,Z) are ± 30 Million, INT_MAX is an arbitrary error value that isn't valid for MC(i.e, (-1, -1)) 
        int biomeMatch = (bID != -INT_MAX && bID == getBiomeAt(&biomeGenerator, 1, spawn.x, 0, spawn.z));
        int structureMatch = 0;

        if (sID != -INT_MAX) {
            Pos structure = findNearestStructure(sID, spawn.x, spawn.z, radiusFromSpawn, biomeGenerator);
            structureMatch = (structure.x != -INT_MAX && structure.z != -INT_MAX);
        }
        /**
         * All possible conditions where we increase the number of seeds we found
         * biome and structure, biome only, structure only
        */

        if ((bID != -INT_MAX && sID != -INT_MAX && biomeMatch && structureMatch) ||
            (bID != -INT_MAX && sID == -INT_MAX && biomeMatch) ||
            (bID == -INT_MAX && sID != -INT_MAX && structureMatch)) {

            foundSeeds[amountFound++] = (SeedEntry) {seed, spawn};
            if (amountFound == numSeeds) {
                printf(numSeeds == 1 ? "Found %d seed.\n" : "Found %d seeds.\n" , amountFound);
                break;
            }
        }
    }

    if (amountFound == 0) {
        printf("No seeds found.\n");
        return (SeedArray){ .seeds = NULL, .length = 0, };
    }

    return (SeedArray){ .seeds = foundSeeds, .length = amountFound};
}