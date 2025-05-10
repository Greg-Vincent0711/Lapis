#include "../../../external/cubiomes/finders.h"
#include <stdio.h>
#include "limits.h"

/**
 * corresponds to !nearest <structure_id> coords range for Lapis
 * Bedrock is not 100% accurate when using this function, diff structure gen than Java
*/
Pos findNearestStructure(enum StructureType sType, int blockX, int blockZ, int maxRadius, Generator bg) {
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
                if (getStructurePos(sType, bg.mc, bg.seed, regionX, regionZ, &structurePos)) {
                    // after a block position is found, check if it's viable
                    if (!isViableStructurePos(sType, &bg, structurePos.x, structurePos.z, 0)) {
                        continue;
                    }

                    // compare the current distance for each X,Z coordinate with the current min
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

        if (minDistSq != LONG_MAX) {
            // 512L refers to the total radius covered by each consecutive ring(hence the +1) in the search 
            long nextMaxPossibleDist = ((long)currentRadius + 1) * 512L;
            nextMaxPossibleDist *= nextMaxPossibleDist;
            /**
             * Essentially, if the squared distance to the current found structure is less
             * than the next radius, break. Don't keep looking for new structures.
            */
            if (minDistSq <= nextMaxPossibleDist) {
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