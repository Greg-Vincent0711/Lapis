# Compiler
CC = gcc

# Compiler flags - Cubiomes as header, integer overflow wraparound
CFLAGS = -I../external/cubiomes -fwrapv

CFLAGS_TEST = $(CFLAGS) -DUNIT_TEST

# Linker flags - Cubiomes static lib, math library
LDFLAGS = ../../external/cubiomes/libcubiomes.a -lm

# Source files
SRCS = \
    inputHandler.c \
    nearestBiome/nearestBiome.c \
    nearestStructure/nearestStructure.c \
    spawnNear/spawnNear.c \
    utilityFns/utilityFns.c

# Object files
OBJS = $(addprefix build/, $(notdir $(SRCS:.c=.o)))


# Output binary
TARGET = inputHandler

# Default build target
all: $(TARGET)

# Rule to link the final binary
$(TARGET): $(OBJS)
	$(CC) -o $@ $^ $(LDFLAGS)

# Rule to build individual object files into the build/ directory
build/%.o:
	@mkdir -p build
	$(CC) $(CFLAGS) -c $(shell find . -name "$*.c") -o $@

# Run with a fixed seed input
try: $(TARGET)
	./$(TARGET) 6815923762915875509 nearest ocean 0 0 3 200

# -----------------------
# Testing configuration
# -----------------------

# Test sources
TEST_SRCS = tests/nearestBiome/test_nearestB.c tests/dependencies/unity.c

# Test object files
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


# Rule to build the test binary
$(TEST_BIN): $(TEST_SRCS) $(TEST_OBJS)
	$(CC) $(CFLAGS) -DUNIT_TEST $^ -o $@ $(LDFLAGS) -I./tests


# Run tests
test: $(TEST_BIN)
	./$(TEST_BIN)

# -----------------------
# Cleaning
# -----------------------

clean:
	rm -rf */*.o */*.a build/*

cleanExec: clean
	rm -f $(TARGET)

cleanTest:
	rm -f $(TEST_BIN) tests/**/*.o

# -----------------------
# Help command
# -----------------------

.PHONY: all test clean cleanAll cleanTest try help

help:
	@echo "Available make commands:"
	@grep -E '^[a-zA-Z_-]+:([^=]|$$)' Makefile | grep -v '^\.' | awk -F':' '{print "  - " $$1}'
