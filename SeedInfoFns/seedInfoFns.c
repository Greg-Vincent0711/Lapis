#include <stdio.h>
#include <string.h>
#include "generator.h"
#include "finders.h"
#include "seedUtility.h"
#include "biomes.h"
#include "limits.h"

Generator biomeGenerator;
uint64_t TEST_SEED = 6815923762915875509;

void setUpBiomeGenerator(){
    setupGenerator(&biomeGenerator, MC_NEWEST, 0);
    applySeed(&biomeGenerator, DIM_OVERWORLD, TEST_SEED);
}
/**
 * corresponds to !nearest command for Lapis
 * for now, the seed is going to have to be hardcoded
 * returns 2d coords for biome (x and z)
 * Not super accurate, need to test
*/
Pos nearestBiome(char *biome, int xCoord, int yCoord, int zCoord, int range, enum BiomeID bID){ 
    setUpBiomeGenerator();
    if (bID < 0) {
        fprintf(stderr, "Error: Unknown biome name '%s'\n", biome);
        return (Pos){-1, -1};
    }
    uint64_t rand = 1;
    uint64_t validBiome = (1ULL << bID);
    setSeed(&rand, TEST_SEED);
    return locateBiome(&biomeGenerator, 
                        xCoord, yCoord, zCoord, range, validBiome, 0, &rand, NULL); 
}

Pos findNearestStructure(enum StructureType sType, int blockX, int blockZ, int maxRadius) {
    Pos nearest = {0};
    long minDistSq = LONG_MAX;
    int startRegionX = blockX >> 9;
    int startRegionZ = blockZ >> 9;
    int maxRegionRadius;
    long maxBlockDistSq = LONG_MAX;

    // block based radius
    if (maxRadius >= 11) {
        maxBlockDistSq = (long)maxRadius * (long)maxRadius;
        maxRegionRadius = (maxRadius >> 9) + 2;
    // region-based radius 
    } else {
        maxRegionRadius = maxRadius;
    }

    for (int currentRadius = 0; currentRadius <= maxRegionRadius; currentRadius++) {
        for (int dx = -currentRadius; dx <= currentRadius; dx++) {
            for (int dz = -currentRadius; dz <= currentRadius; dz++) {
                // Only check edges of the current ring
                if (abs(dx) != currentRadius && abs(dz) != currentRadius)
                    continue;

                int regionX = startRegionX + dx;
                int regionZ = startRegionZ + dz;

                Pos structurePos;
                if (getStructurePos(sType, biomeGenerator.mc, biomeGenerator.seed, regionX, regionZ, &structurePos)) {
                    if (!isViableStructurePos(sType, &biomeGenerator, structurePos.x, structurePos.z, 0)) {
                        continue;
                    }

                    long distanceX = structurePos.x - blockX;
                    long distanceZ = structurePos.z - blockZ;
                    long distanceSq = distanceX * distanceX + distanceZ * distanceZ;

                    if (distanceSq < minDistSq) {
                        // only save locations within the maxBlock distance if using block radius
                        if (maxRadius >= 11 && distanceSq > maxBlockDistSq)
                            continue;
                        minDistSq = distanceSq;
                        nearest = structurePos;
                    }
                }
            }
        }

        if (minDistSq != LONG_MAX) {
            // farthest possible distance from the current radius is 512 blocks
            long maxPossibleDist = ((long)currentRadius + 1) * 512L;
            maxPossibleDist *= maxPossibleDist;
            if (minDistSq <= maxPossibleDist) {
                break;
            }
        }
    }

    if (minDistSq == LONG_MAX) {
        nearest.x = -1;
        nearest.z = -1;
    }

    return nearest;
}



Pos nearestStructure(enum StructureType sType, int blockX, int blockZ, int maxRadius){
    setUpBiomeGenerator();
    // int structureCheck = isViableStructurePos(sType, &biomeGenerator, blockX << 4, blockZ << 4, 0);
    // printf("%d", structureCheck);
    Pos structureCoords = findNearestStructure(sType, blockX, blockZ, maxRadius);
    if (structureCoords.x == -1 && structureCoords.z == -1) {
        printf("No structure found within range.\n");
    }
    return structureCoords;
}

/**
 * !nearestBiome
 * !nearest
 * !random
 * !spawn_near
 * !locate
*/
int main(int argc, char *argv[]){
    char *command = argv[1];
    char *argument = argv[2];
    printf("%s %s \n", command, argument);
    if(strcmp(command, "nearest") == 0){
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
            int xCoord = atoi(argv[3]);
            int zCoord = atoi(argv[4]);
            int range = atoi(argv[5]);
            printf("%d %d %d\n", xCoord, zCoord, range);
            // Bedrock is 100% accurate when using this function, diff structure gen than Java
            Pos structureCoords = nearestStructure(sType, xCoord, zCoord, range);
            printf("Nearest %s: %d, %d", argument, structureCoords.x, structureCoords.z);
        } else {
            printf("Invalid argument. Make sure you used the correct Biome or Structure name. Check spelling.\n");
        }
        
    } else if(strcmp(command, "spawn_near")){

    } else if(strcmp(command, "locate")){

    } else{

    }
    return 0;
}

// ./seedInfoFns 'nearestBiome' plains 0 0 0 1024