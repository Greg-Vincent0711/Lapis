// test_biomes.c
#include "../dependencies/unity.h"
#include "../../inputHandler.h"
#include "../../nearestBiome/nearestBiome.h"
#include "../../utilityFns/utilityFns.h"
#include "../../../external/cubiomes/finders.h"

void setUp(void){}
void tearDown(void){}


void test_biome_found() {
    const Generator g = setUpBiomeGenerator(1234);
    enum BiomeID bID = get_biome_id("plains");
    Pos result = nearestBiome("plains", 0, 64, 0, 1000, bID, g);
    TEST_ASSERT_NOT_EQUAL(-INT_MAX, result.x);
    TEST_ASSERT_NOT_EQUAL(-INT_MAX, result.z);
}

// void test_invalidCoordinates(){
//     const Generator g = makeTestGenerator();
//     enum BiomeID bID = get_biome_id("plains");
//     Pos result = nearestBiome("x", 0, 64, 0, 1000, bID, g);
// }



int main(void) {
    UNITY_BEGIN();
    RUN_TEST(test_biome_found);
    return UNITY_END();
}

// compiling and running
// gcc test_biomes.c unity.c ../../../external/cubiomes/*.c -o test_runner -lm
// ./test_runner


