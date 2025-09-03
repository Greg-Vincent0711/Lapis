CC = gcc

# Compiler flags - Cubiomes as header, integer overflow wraparound
CFLAGS = -I../external/cubiomes -fwrapv

# when testing, we don't want inputHandler main to be an entry point
# so add the UNIT_TEST flag with -D
CFLAGS_TEST = $(CFLAGS) -DUNIT_TEST

# Linker flags - Cubiomes static lib, math library
LDFLAGS = ../../external/cubiomes/libcubiomes.a -lm

SRCS = \
    inputHandler.c \
    nearestBiome/nearestBiome.c \
    nearestStructure/nearestStructure.c \
    spawnNear/spawnNear.c \
    utilityFns/utilityFns.c

OBJS = $(addprefix build/, $(notdir $(SRCS:.c=.o)))

# Output binary
TARGET = inputHandler

all: $(TARGET)

# Rule to link the final binary
$(TARGET): $(OBJS)
	$(CC) -o $@ $^ $(LDFLAGS)

# auto find all the .c files, compile to .o
build/%.o:
	@mkdir -p build
	$(CC) $(CFLAGS) -c $(shell find . -name "$*.c") -o $@

try: $(TARGET)
	./$(TARGET) 6815923762915875509 nearest ocean 0 0 3 200

# update this for every new test you create
TEST_SRCS = \
	tests/test_runner.c \
	tests/nearestBiome/test_nearestB.c \
	tests/nearestStructure/test_nearestS.c \
	tests/spawnNear/test_spawnN.c \
	tests/dependencies/unity.c

TEST_OBJS = \
	build/inputHandler_test.o \
    build/nearestBiome.o \
    build/utilityFns.o \
    build/spawnNear.o \
    build/nearestStructure.o

# Test binary name
TEST_BIN = seedInfo_tests

build/inputHandler_test.o:
	@mkdir -p build
	$(CC) $(CFLAGS_TEST) -c inputHandler.c -o build/inputHandler_test.o

# test binary
$(TEST_BIN): $(TEST_SRCS) $(TEST_OBJS)
	$(CC) $(CFLAGS) -DUNIT_TEST $^ -o $@ $(LDFLAGS) -I./tests

test: $(TEST_BIN)
	./$(TEST_BIN)

clean:
	rm -rf */*.o */*.a build/*

cleanExec: clean
	rm -f $(TARGET)

cleanTest:
	rm -f $(TEST_BIN) tests/**/*.o

remakeTest:
	rm -f $(TEST_BIN) tests/**/*.o
	$(MAKE) test


.PHONY: all test clean cleanAll cleanTest remakeTest try help 

help:
	@echo "Available make commands:"
	@grep -E '^[a-zA-Z_-]+:([^=]|$$)' Makefile | grep -v '^\.' | awk -F':' '{print "  - " $$1}'
