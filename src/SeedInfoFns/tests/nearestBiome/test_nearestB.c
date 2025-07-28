// test_biomes.c
#include "../dependencies/unity.h"
#include "../../inputHandler.h"
#include "../../nearestBiome/nearestBiome.h"
#include "../../utilityFns/utilityFns.h"
#include "../../../external/cubiomes/finders.h"

void test_biome_found() {
    const Generator g = setUpBiomeGenerator(1234);
    enum BiomeID bID = get_biome_id("plains");
    Pos result = nearestBiome("plains", 0, 64, 0, 1000, bID, g);
    printf("%d, %d", result.x, result.z);
    TEST_ASSERT_NOT_EQUAL(-INT_MAX, result.x);
    TEST_ASSERT_NOT_EQUAL(-INT_MAX, result.z);
}

void test_invalidBiomeName(){
    const Generator g = setUpBiomeGenerator(1234);
    enum BiomeID bID = get_biome_id("playland");
    Pos result = nearestBiome("x", 0, 64, 0, 1000, bID, g);
    TEST_ASSERT_EQUAL(-INT_MAX, result.x);
    TEST_ASSERT_EQUAL(-INT_MAX, result.z);
}

// compiling and running
// gcc test_biomes.c unity.c ../../../external/cubiomes/*.c -o test_runner -lm
// ./test_runner


