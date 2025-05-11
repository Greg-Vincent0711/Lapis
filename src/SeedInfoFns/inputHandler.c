/**
 * TODO
 * - Dimension, Seed, MC_Version should be user set fields
 * - So, the backend needs to require those fields. Work on this
 * - Start Lapis code portion to interact with backend
 * - Write tests for cubiomes code and lapis
 * - Switch architecture to hosting 
*/

#include <stdio.h>
#include <string.h>
#include "limits.h"

#include "../../external/cubiomes/finders.h"
#include "../../external/cubiomes/biomes.h"
#include "./nearestBiome/nearestBiome.h"
#include "./nearestStructure/nearestStructure.h"
#include "./spawnNear/spawnNear.h"
#include "./utilityFns/utilityFns.h"

// will be gone soon
uint64_t TEST_SEED = 6815923762915875509;

Generator setUpBiomeGenerator(){
    Generator biomeGenerator;
    setupGenerator(&biomeGenerator, MC_NEWEST, 0);
    applySeed(&biomeGenerator, DIM_OVERWORLD, TEST_SEED);
    return biomeGenerator;
}

/**
 * 3 command types
 * nearest structure
 * nearest village
 * spawn_near
*/
int main(int argc, char *argv[]){
    Generator biomeGenerator = setUpBiomeGenerator();
    char *command = argv[1];
    char *argument = argv[2];
    if(strcmp(command, "nearest") == 0){
        enum BiomeID bID = get_biome_id(argument);
        enum StructureType sType = get_structure_id(argument); 
        if(bID != -1){
            if (argc < 7) {
                printf("Usage (Biome): ./inputHandler nearest <biomeName> <x> <y> <z> <range>\n");
                return -1;
            }
            int xCoord = atoi(argv[3]);
            int yCoord = atoi(argv[4]);
            int zCoord = atoi(argv[5]);
            int searchRange = atoi(argv[6]);
            // accurate between Bedrock and Java since they share the same world gen
            Pos biomeCoords = nearestBiome(argument, xCoord, yCoord, zCoord, searchRange, bID, biomeGenerator);
            printf("Nearest %s: %d, %d", argument, biomeCoords.x, biomeCoords.z);
        } else if(sType != -1){
            if (argc < 6) {
                printf("Usage (Structure): ./inputHandler nearest <structureName> <x> <z> <range>\n");
                return -1;
            }
            int xCoord = atoi(argv[3]);
            int zCoord = atoi(argv[4]);
            int range = atoi(argv[5]);
            printf("%d %d %d\n", xCoord, zCoord, range);
            Pos structureCoords = findNearestStructure(sType, xCoord, zCoord, range, biomeGenerator);
            printf("Nearest %s: %d, %d", argument, structureCoords.x, structureCoords.z);
        } else {
            fprintf(stderr, "Invalid argument. Make sure you used the correct Biome or Structure name. Check spelling.\n");
            return -1;
        }
    } else if(strcmp(command, "spawn_near") == 0){
        if (argc < 6) {
            printf("Usage: ./inputHandler spawn_near numseeds biome structure range\n");
            return -1;
        }
        int numSeeds = atoi(argv[2]);
        char* biome = argv[3];
        char* structure = argv[4];
        int range = atoi(argv[5]);
        SeedArray seedData = spawnNear(numSeeds, biome, structure, range, biomeGenerator);
        for (int i = 0; i < seedData.length; i++){
            int xCoord = seedData.seeds[i].spawnCoordinates.x;
            int zCoord = seedData.seeds[i].spawnCoordinates.z;
            printf("Found Seed: %llu with spawn: %d %d \n", seedData.seeds[i].seed, xCoord, zCoord);
        }
        free(seedData.seeds);
        return 0;

    } else {
        printf("Invalid command. Check the list of all possible commands and try again.\n");
        return 0;
    }
}
