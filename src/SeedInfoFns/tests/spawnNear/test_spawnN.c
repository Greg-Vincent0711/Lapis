#include "../dependencies/unity.h"
#include "../../inputHandler.h"
#include "../../spawnNear/spawnNear.h"
#include "../../utilityFns/utilityFns.h"

void test_valid_biome_only() {
    Generator g = setUpBiomeGenerator(123456789);
    SeedArray result = spawnNear(1, "plains", "None", 500, g);
    TEST_ASSERT_NOT_NULL(result.seeds);
    TEST_ASSERT_EQUAL(1, result.length);
    free(result.seeds);
}

void test_valid_structure_only() {
    Generator g = setUpBiomeGenerator(987654321);
    SeedArray result = spawnNear(1, "None", "Village", 1000, g);
    TEST_ASSERT_NOT_NULL(result.seeds);
    TEST_ASSERT_NOT_EQUAL(0, result.length);
    free(result.seeds);
}


void test_invalid_parameters() {
    Generator g = setUpBiomeGenerator(5555);
    SeedArray result = spawnNear(1, "NotARealBiome", "NotARealStructure", 500, g);
    TEST_ASSERT_NULL(result.seeds);
    TEST_ASSERT_EQUAL(0, result.length);
}


void test_valid_biome_and_structure() {
    Generator g = setUpBiomeGenerator(111222333);
    SeedArray result = spawnNear(1, "Plains", "Village", 1500, g);
    TEST_ASSERT_NOT_NULL(result.seeds);
    TEST_ASSERT_EQUAL(1, result.length);
    free(result.seeds);
}
