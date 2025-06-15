/**
     * In future versions, add ability to change how many seeds can be searched
     * For free version, 1,000,000 is fine
     * TODO - add support for end and nether in future versions
     
**/

#include "stdio.h"
#include "string.h"
#include "../../../external/cubiomes/finders.h"
#include "limits.h"
#include "../utilityFns/utilityFns.h"
#include "../nearestStructure/nearestStructure.h"

/**
 * Return seeds with certain spawn conditions. User will not directly pass the bot every single field.
 * Returns a seed or multiple with the specified spawn conditions
 * Read parameters as: x seeds where I spawn in this biome, with a structure x blocks from spawn
*/
SeedArray spawnNear(int numSeeds, char* biome, char* structure, int radiusFromSpawn, Generator biomeGenerator) {
    // max params are subject to change
    const int MAX_RADIUS = 3000;
    const int MAX_SEEDS = 10;
    char* DefaultForUnused = "None";
    if (numSeeds <= 0 || numSeeds > MAX_SEEDS) {
        printf("{ \"error\": \"Invalid number of seeds requested. Must be greater than 0 and no greater than %d.\" }", MAX_SEEDS);
        return (SeedArray){ .seeds = NULL, .length = 0 };
    }

    int bID = strcmp(biome, DefaultForUnused) ? get_biome_id(biome) : -1;
    int sID = strcmp(structure, DefaultForUnused) ? get_structure_id(structure) : -1;
    
    if (bID == -1 && sID == -1) {
        printf("{ \"error\": \"Check your spelling. You must provide either an allowed biome or structure as a search parameter.\" }");
        return (SeedArray){ .seeds = NULL, .length = 0 };
    }

    if (radiusFromSpawn <= 0 || radiusFromSpawn > MAX_RADIUS) {
        printf("{ \"error\": \"Invalid radius. Must be greater than 0 and no greater than %d.\" }", MAX_RADIUS);
        return (SeedArray){ .seeds = NULL, .length = 0 };
    }

    SeedEntry* foundSeeds = malloc(sizeof(SeedEntry) * numSeeds);
    if (!foundSeeds) {
        printf("{ \"error\": \"Memory allocation failed\" }");
        return (SeedArray){ .seeds = NULL, .length = 0 };
    }

    int amountFound = 0;
    int seedSearchLimit = 1000000;
    uint64_t seedStart = generate_random_seed(seedSearchLimit);
    for (uint64_t seed = seedStart; seed < seedStart + seedSearchLimit; seed++) {
        applySeed(&biomeGenerator, biomeGenerator.dim, seed);
        // getSpawn fn is not 100% accurate
        Pos spawn = getSpawn(&biomeGenerator);
        int biomeMatch = (bID != -1 && bID == getBiomeAt(&biomeGenerator, 1, spawn.x, 0, spawn.z));
        int structureMatch = 0;

        if (sID != -1) {
            // MC coords(X,Z) are ± 30 Million, INT_MAX is an arbitrary error value that isn't valid for MC(i.e, (-1, -1)) 
            Pos structure = findNearestStructure(sID, spawn.x, spawn.z, radiusFromSpawn, biomeGenerator);
            structureMatch = (structure.x != -INT_MAX && structure.z != -INT_MAX);
        }
        /**
         * All possible conditions where we increase the number of seeds we found
         * biome and structure, biome only, structure only
        */

        if ((bID != -1 && sID != -1 && biomeMatch && structureMatch) ||
            (bID != -1 && sID == -1 && biomeMatch) ||
            (bID == -1 && sID != -1 && structureMatch)) {

            foundSeeds[amountFound++] = (SeedEntry) {seed, spawn};
            if (amountFound == numSeeds) {
                // printf(numSeeds == 1 ? "Found %d seed.\n" : "Found %d seeds.\n" , amountFound);
                break;
            }
        }
    }

    if (amountFound == 0) {
        printf("{ \"message\": \"No seeds found.\" }");
        return (SeedArray){ .seeds = NULL, .length = 0, };
    }

    return (SeedArray){ .seeds = foundSeeds, .length = amountFound};
}
