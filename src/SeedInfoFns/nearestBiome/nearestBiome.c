#include <stdio.h>
#include "limits.h"
#include "../../../external/cubiomes/finders.h"
Pos nearestBiome(char *biome, int xCoord, int yCoord, int zCoord, int range, enum BiomeID bID, Generator bg){ 
    if (bID < 0) {
        fprintf(stderr, "Error: Unknown biome name '%s'\n", biome);
        return (Pos){-INT_MAX, -INT_MAX};
    }
    // rand value is arbitrary
    uint64_t rand = 1;
    uint64_t validBiome = (1ULL << bID);
    setSeed(&rand, bg.seed);
    return locateBiome(&bg, 
                        xCoord, yCoord, zCoord, range, validBiome, 0, &rand, NULL); 
}