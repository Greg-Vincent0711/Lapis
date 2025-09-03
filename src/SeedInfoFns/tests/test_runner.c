#include "./dependencies/unity.h"
#include "./nearestBiome/test_nearestB.h"
#include "./nearestStructure/test_nearestS.h"
#include "./spawnNear/test_spawnN.h"

// potentially add more tests in the future
void setUp(void){}
void tearDown(void){}

int main(void) {
    UNITY_BEGIN();
    // biome tests
    RUN_TEST(test_biome_found);
    RUN_TEST(test_invalidBiomeName);

    // structure tests
    RUN_TEST(test_valid_input_structure_found);
    RUN_TEST(test_valid_input_structure_not_found);

    // spawn near tests
    RUN_TEST(test_valid_biome_only);
    RUN_TEST(test_valid_structure_only);
    RUN_TEST(test_invalid_parameters);
    RUN_TEST(test_valid_biome_and_structure);
    return UNITY_END();
}


// compiling and running
// gcc test_biomes.c unity.c ../../../external/cubiomes/*.c -o test_runner -lm
// ./test_runner
