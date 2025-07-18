// test_biomes.c
#include "src/SeedInfoFns/tests/unity.h"
#include "../../../external/cubiomes/finders.h"

extern Pos nearestBiome(char*, int, int, int, int, enum BiomeID, Generator);

void setUp(void) {}
void tearDown(void) {}

void test_biome_found(void) {
    Generator g;
    initBiomeGenerator(&g, MC_1_16);
    applySeed(&g, 1234);
    Pos result = nearestBiome("plains", 0, 64, 0, 1000, biomePlains, g);
    TEST_ASSERT_NOT_EQUAL(-INT_MAX, result.x);
    TEST_ASSERT_NOT_EQUAL(-INT_MAX, result.z);
}

int main(void) {
    UNITY_BEGIN();
    RUN_TEST(test_biome_found);
    return UNITY_END();
}
