/**
 * TODO
 * - Start Lapis code portion to interact with backend
 * - Write tests for cubiomes code and lapis
 * - Switch architecture to hosting 
*/

#include <stdio.h>
#include <string.h>
#include "limits.h"
#include <errno.h>
#include "../../external/cubiomes/finders.h"
#include "../../external/cubiomes/biomes.h"
#include "./nearestBiome/nearestBiome.h"
#include "./nearestStructure/nearestStructure.h"
#include "./spawnNear/spawnNear.h"
#include "./utilityFns/utilityFns.h"


Generator setUpBiomeGenerator(uint64_t seed){
    Generator biomeGenerator;
    setupGenerator(&biomeGenerator, MC_NEWEST, 0);
    applySeed(&biomeGenerator, DIM_OVERWORLD, seed);
    return biomeGenerator;
}

/**
 * nearest structure
 * nearest village
 * spawn_near
 * When strictly using the backend, a seed must be passed
 * Lapis will hold onto seeds(and eventually some other info) for players.
*/

int main(int argc, char *argv[]){
    // ptr checks for string validity, and we need base 10
    char* end;
    // global error handler
    errno = 0;
    uint64_t seed = (uint64_t) strtoull(argv[1], &end, 10);

    if(strcmp(end, "\0") || errno == ERANGE){
        // printf("Seed input is invalid.\n");
        printf("{\"Error\": \"Seed input is invalid.\"}\n");
        return -1;
    }

    Generator biomeGenerator = setUpBiomeGenerator(seed);
    char *command = argv[2];
    char *argument = argv[3];
    if(strcmp(command, "nearest") == 0){
        enum BiomeID bID = get_biome_id(argument);
        enum StructureType sType = get_structure_id(argument); 
        if(bID != -1){
            if (argc < 8) {
                printf("{\"Error\": \"Incorrect usage. Amount of arguments is too low.\"}\n");
                return -1;
            }
            int xCoord = atoi(argv[4]);
            int yCoord = atoi(argv[5]);
            int zCoord = atoi(argv[6]);
            int searchRange = atoi(argv[7]);
            // accurate between Bedrock and Java since they share the same world gen
            Pos biomeCoords = nearestBiome(argument, xCoord, yCoord, zCoord, searchRange, bID, biomeGenerator);
            printf("{\"feature\": \"%s\", \"x\": %d, \"z\": %d}\n", argument, biomeCoords.x, biomeCoords.z);
            return 0;
        } else if(sType != -1){
            if (argc < 7) {
                printf("{\"Error\": \"Incorrect usage. Amount of arguments is too low for.\"}\n");
                return -1;
            }
            int xCoord = atoi(argv[4]);
            int zCoord = atoi(argv[5]);
            int range = atoi(argv[6]);
            Pos structureCoords = findNearestStructure(sType, xCoord, zCoord, range, biomeGenerator);
            printf("{\"feature\": \"%s\", \"x\": %d, \"z\": %d}\n", argument, structureCoords.x, structureCoords.z);
            return 0;
        } else {
            printf("{\"Error\": \"Incorrect usage.\"}\n");
            return -1;
        }
    } else if(strcmp(command, "spawn_near") == 0){
        if (argc < 7) {
            printf("{ \"usage\": \"./inputHandler seed spawn_near numseeds biome structure range\" }\n");
            return -1;
        }
        int numSeeds = atoi(argv[3]);
        char* biome = argv[4];
        char* structure = argv[5];
        int range = atoi(argv[6]);
        SeedArray seedData = spawnNear(numSeeds, biome, structure, range, biomeGenerator);
        if(seedData.length != 0 && seedData.seeds != NULL){
            printf("[\n");
            for (int i = 0; i < seedData.length; i++) {
                int xCoord = seedData.seeds[i].spawnCoordinates.x;
                int zCoord = seedData.seeds[i].spawnCoordinates.z;
                printf("{\"seed\": %llu, \"spawn\": {\"x\": %d, \"z\": %d}}", seedData.seeds[i].seed, xCoord, zCoord);
                if (i < seedData.length - 1) {
                    printf(",\n");
                } else {
                    printf("\n");
                }
            }
            printf("]\n");
            free(seedData.seeds);
        }
        return 0;

    } else {
        printf("{\"seed\": none, \"spawn\": {\"x\": 0, \"z\": 0}}\n");
        return 0;
    }
}
