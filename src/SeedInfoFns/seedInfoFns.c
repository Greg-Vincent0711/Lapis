#include <stdio.h>
#include <string.h>
#include "../../external/cubiomes/finders.h"
#include "seedUtility.h"
#include "../../external/cubiomes/biomes.h"
#include "limits.h"

Generator biomeGenerator;
uint64_t TEST_SEED = 6815923762915875509;

/**
 * TODO - Dimension should be editable based on what the user wants to search for
 * Same with MC version. 
 * Should be editable on frontend
*/
void setUpBiomeGenerator(){
    setupGenerator(&biomeGenerator, MC_NEWEST, 0);
    applySeed(&biomeGenerator, DIM_OVERWORLD, TEST_SEED);
}

/**
 * Corresponds to !nearest <biome> coords range for Lapis
 * for now, the seed is going to have to be hardcoded
 * returns 2d coords for biome (x and z)
 * Relatively accurate for Bedrock and Java, since they share the same world gen
*/
Pos nearestBiome(char *biome, int xCoord, int yCoord, int zCoord, int range, enum BiomeID bID){ 
    setUpBiomeGenerator();
    if (bID < 0) {
        fprintf(stderr, "Error: Unknown biome name '%s'\n", biome);
        return (Pos){-INT_MAX, -INT_MAX};
    }
    uint64_t rand = 1;
    uint64_t validBiome = (1ULL << bID);
    setSeed(&rand, TEST_SEED);
    return locateBiome(&biomeGenerator, 
                        xCoord, yCoord, zCoord, range, validBiome, 0, &rand, NULL); 
}

/**
 * corresponds to !nearest <structure_id> coords range for Lapis
 * Bedrock is not 100% accurate when using this function, diff structure gen than Java
*/
Pos findNearestStructure(enum StructureType sType, int blockX, int blockZ, int maxRadius) {
    Pos nearest = {0};
    // initialize first
    long minDistSq = LONG_MAX;
    long maxBlockDistSq = LONG_MAX;

    /**
     * region coordinates represent 512 blocks at a time
     * right-shifting by 9 switches coordinates to region coords
    */
    int startRegionX = blockX >> 9;
    int startRegionZ = blockZ >> 9;
    int maxRegionRadius;
    

    /**
     * if the maxRadius is 10 or less, treat it like a region radius (maxRadius << 9)
     * Past 10, it doesn't seem too practical, since most structures a player wants to find
     * are probably within a 5120 block radius. 
    */
    if (maxRadius >= 11) {
        maxBlockDistSq = (long)maxRadius * (long)maxRadius;
        maxRegionRadius = (maxRadius >> 9) + 2;
    } else {
        maxRegionRadius = maxRadius;
    }

    for (int currentRadius = 0; currentRadius <= maxRegionRadius; currentRadius++) {
        for (int dx = -currentRadius; dx <= currentRadius; dx++) {
            for (int dz = -currentRadius; dz <= currentRadius; dz++) {
                if (abs(dx) != currentRadius && abs(dz) != currentRadius){
                    continue;
                }
                int regionX = startRegionX + dx;
                int regionZ = startRegionZ + dz;


                Pos structurePos;
                // getStructurePos updates the Pos passed to it in-place
                if (getStructurePos(sType, biomeGenerator.mc, biomeGenerator.seed, regionX, regionZ, &structurePos)) {
                    // after a block position is found, check if it's viable
                    if (!isViableStructurePos(sType, &biomeGenerator, structurePos.x, structurePos.z, 0)) {
                        continue;
                    }

                    // compare the distance for each X,Z coordinate with the current min
                    long distanceX = structurePos.x - blockX;
                    long distanceZ = structurePos.z - blockZ;
                    long distanceSq = distanceX * distanceX + distanceZ * distanceZ;

                    if (distanceSq < minDistSq) {
                        // only save locations within the maxBlock distance if using block radius
                        if (maxRadius >= 11 && distanceSq > maxBlockDistSq)
                            continue;
                        // otherwise, update the nearest Pos 
                        minDistSq = distanceSq;
                        nearest = structurePos;
                    }
                }
            }
        }

    // check if a closer structure exists in any future regions
        if (minDistSq != LONG_MAX) {
            // check within the next max possible radius
            long maxPossibleDist = ((long)currentRadius + 1) * 512L;
            // for distance, use squared over sqrt for performance
            maxPossibleDist *= maxPossibleDist;
            if (minDistSq <= maxPossibleDist) {
                break;
            }
        }
    }

    if (minDistSq == LONG_MAX) {
        nearest.x = -INT_MAX;
        nearest.z = -INT_MAX;
    }

    return nearest;
}



Pos nearestStructure(enum StructureType sType, int blockX, int blockZ, int maxRadius){
    setUpBiomeGenerator();
    Pos structureCoords = findNearestStructure(sType, blockX, blockZ, maxRadius);
    if (structureCoords.x == -INT_MAX && structureCoords.z == -INT_MAX) {
        printf("No structure found within range.\n");
    }
    return structureCoords;
}


/**
 * Returns a seed or multiple with the specified spawn conditions
 *  0<= radiusFromSpawn <= 3000 blocks
*/
SeedArray spawnNear(int numSeeds, char* biome, char* structure, int radiusFromSpawn) {
    if (numSeeds <= 0) {
        fprintf(stderr, "Invalid number of seeds requested\n");
        return (SeedArray){ .seeds = NULL, .length = 0 };
    }

    int bID = get_biome_id(biome);
    int sID = structure != 'None' ? get_structure_id(structure) : -INT_MAX;
    
    if (bID == -INT_MAX && sID == -INT_MAX) {
        fprintf(stderr, "Check your spelling. You must provide either a biome or structure as a search parameter.\n");
        return (SeedArray){ .seeds = NULL, .length = 0 };
    }

    if (radiusFromSpawn <= 0 || radiusFromSpawn > 3000) {
        fprintf(stderr, "Invalid radius. Must be greater than 0 and no greater than 3000.\n");
        return (SeedArray){ .seeds = NULL, .length = 0 };
    }

    setUpBiomeGenerator();
    SeedEntry* foundSeeds = malloc(sizeof(SeedEntry) * numSeeds);
    if (!foundSeeds) {
        fprintf(stderr, "Memory allocation failed\n");
        return (SeedArray){ .seeds = NULL, .length = 0 };
    }

    int amountFound = 0;
    int limit = 1000000;
    uint64_t seedStart = generate_random_seed(limit);
    for (uint64_t seed = seedStart; seed < seedStart + limit; seed++) {
        applySeed(&biomeGenerator, DIM_OVERWORLD, seed);
        // not entirely accurate, but good enough
        Pos spawn = getSpawn(&biomeGenerator);

        int biomeMatch = (bID != -INT_MAX && bID == getBiomeAt(&biomeGenerator, 1, spawn.x, 0, spawn.z));
        int structureMatch = 0;

        if (sID != -INT_MAX) {
            Pos structure = findNearestStructure(sID, spawn.x, spawn.z, radiusFromSpawn);
            structureMatch = (structure.x != -INT_MAX && structure.z != -INT_MAX);
        }

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



/**
 * !nearest - Biome & Structure
 * !spawn_near
*/
int main(int argc, char *argv[]){
    char *command = argv[1];
    char *argument = argv[2];
    if(strcmp(command, "nearest") == 0){
        if (argc < 7) {
            printf("Usage (Biome): ./seedInfoFns nearest <biomeName|structureName> <x> <y> <z> <range>\n");
            return -1;
        }
        enum BiomeID bID = get_biome_id(argument);
        enum StructureType sType = get_structure_id(argument);
        if(bID != -1){
            int xCoord = atoi(argv[3]);
            int yCoord = atoi(argv[4]);
            int zCoord = atoi(argv[5]);
            int searchRange = atoi(argv[6]);
            // accurate between Bedrock and Java since they share the same world gen
            Pos biomeCoords = nearestBiome(argument, xCoord, yCoord, zCoord, searchRange, bID);
            printf("Nearest %s: %d, %d", argument, biomeCoords.x, biomeCoords.z);
        } else if(sType != -1){
            if (argc < 6) {
                printf("Usage (Structure): ./seedInfoFns nearest <structureName> <x> <z> <range>\n");
                return -1;
            }
            int xCoord = atoi(argv[3]);
            int zCoord = atoi(argv[4]);
            int range = atoi(argv[5]);
            printf("%d %d %d\n", xCoord, zCoord, range);
            Pos structureCoords = nearestStructure(sType, xCoord, zCoord, range);
            printf("Nearest %s: %d, %d", argument, structureCoords.x, structureCoords.z);
        } else {
            printf("Invalid argument. Make sure you used the correct Biome or Structure name. Check spelling.\n");
            return -1;
        }
    } else if(strcmp(command, "spawn_near") == 0){
        if (argc < 6) {
            printf("Usage: ./seedInfoFns spawn_near numseeds biome structure range \n");
            return -1;
        }
        int numSeeds = atoi(argv[2]);
        char* biome = argv[3];
        char* structure = argv[4];
        int range = atoi(argv[5]);
        SeedArray seedData = spawnNear(numSeeds, biome, structure, range);
        for (int i = 0; i < seedData.length; i++){
            int xCoord = seedData.seeds[i].spawnCoordinates.x;
            int zCoord = seedData.seeds[i].spawnCoordinates.z;
            printf("Found Seed: %llu with spawn: %d %d \n", seedData.seeds[i].seed, xCoord, zCoord);
        }
        free(seedData.seeds);
        return 0;

    } else {
        printf("Invalid command. Check the list of all possible commands and try again.\n");
    }
    return 0;
}
