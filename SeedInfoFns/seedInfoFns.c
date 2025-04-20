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
Pos nearestBiome(char *biome, int xCoord, int yCoord, int zCoord, int range){  
    setUpBiomeGenerator();
    enum BiomeID bID = get_biome_id(biome);
    // mask operation to only allow biome as search parameter
    uint64_t validBiome = (1ULL << bID);
    Pos biomeCoords = locateBiome(&biomeGenerator, 
                        xCoord, yCoord, zCoord, range, validBiome, 0, 0, 0); 
    printf("Pos(x=%d, z=%d)\n", biomeCoords.x, biomeCoords.z);
    return biomeCoords;
}

int nearestStructure(char *structure, char *coordinates){
    Generator biomeGenerator;
    setupGenerator(&biomeGenerator, MC_NEWEST, 0);
    uint64_t TEST_SEED = 6815923762915875509;
    applySeed(&biomeGenerator, DIM_OVERWORLD, TEST_SEED);
    Pos biomeCoordinates;

    int block_scale = 1; // scale=1: block coordinates, scale=4: biome coordinates
    int x = 305, y = 63, z = 931;    
    return 0;
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
    if(strcmp(command, "nearestBiome") == 0){
        int xCoord = atoi(argv[3]);
        int yCoord = atoi(argv[4]); 
        int zCoord = atoi(argv[5]);
        int searchRange = atoi(argv[6]);
        nearestBiome(argument, xCoord, yCoord, zCoord, searchRange);
    } else if(strcmp(command, "!random")){
        
    } else if(strcmp(command, "!spawn_near")){

    } else if(strcmp(command, "!locate")){

    } else{

    }
    return 0;
}

// ./seedInfoFns 'nearestBiome' plains 0 0 0 1024