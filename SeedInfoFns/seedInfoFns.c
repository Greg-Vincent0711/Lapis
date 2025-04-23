#include <stdio.h>
#include <string.h>
#include "generator.h"
#include "finders.h"
#include "seedUtility.h"
#include "biomes.h"

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

Pos nearestStructure(enum StructureType sType, int xCoord, int zCoord){
    setUpBiomeGenerator();
    Pos structureCoords;
    int structureCheck = isViableStructurePos(sType, &biomeGenerator, xCoord, zCoord, 0);
    if (structureCheck == 1){
        getStructurePos(sType, MC_NEWEST, TEST_SEED, xCoord, zCoord, &structureCoords);
        printf("Nearest structure coords, X:%d, Z:%d", structureCoords.x, structureCoords.z);
        return structureCoords;
    } else{
        return (Pos){0, 0};
    }
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
    if(strcmp(command, "nearest") == 0){
        int xCoord = atoi(argv[3]);
        int yCoord = atoi(argv[4]);
        int zCoord = atoi(argv[5]);
        int searchRange = atoi(argv[6]);
        enum BiomeID bID = get_biome_id(argument);
        enum StructureType sType = get_structure_id(argument);
        if(bID != -1){
            Pos biomeCoords = nearestBiome(argument, xCoord, yCoord, zCoord, searchRange, bID);
            printf("Nearest biome: %d, %d", biomeCoords.x, biomeCoords.z);
        } else if(sType != -1){
            Pos structureCoords = nearestStructure(sType, xCoord, zCoord);
            printf("Nearest structure: %d, %d", structureCoords.x, structureCoords.z);
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