#include "../dependencies/unity.h"
#include "../../inputHandler.h"
#include "../../nearestStructure/nearestStructure.h"
#include "../../utilityFns/utilityFns.h"
#include "../../../external/cubiomes/finders.h"

void test_valid_input_structure_found(){
    const Generator g = setUpBiomeGenerator(1234);
    enum StructureType sID = get_structure_id("Mansion");
    Pos result = findNearestStructure(sID, 0, 0, 3000, g);
    printf("%d, %d", result.x, result.z);
    TEST_ASSERT_NOT_EQUAL(-INT_MAX, result.x);
    TEST_ASSERT_NOT_EQUAL(-INT_MAX, result.z);
}

void test_valid_input_structure_not_found(){
    const Generator g = setUpBiomeGenerator(1234);
    enum StructureType sID = get_structure_id("Outpost");
    // no pillager outpost exists within this range of coords on the seed
    Pos result = findNearestStructure(sID, -400, -64, 500, g);
    printf("%d, %d", result.x, result.z);
    // no result could be found
    TEST_ASSERT_EQUAL(-INT_MAX, result.x);
    TEST_ASSERT_EQUAL(-INT_MAX, result.z);
}