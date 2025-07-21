CC = gcc

# Compiler flags - Cubiomes as header, integer overflow wraparound
CFLAGS = -I../external/cubiomes -fwrapv

# Linker flags - Cubiomes static lib, math library
LDFLAGS = ../../external/cubiomes/libcubiomes.a -lm

SRCS = \
    inputHandler.c \
    nearestBiome/nearestBiome.c \
    nearestStructure/nearestStructure.c \
    spawnNear/spawnNear.c \
    utilityFns/utilityFns.c

OBJS = $(addprefix build/, $(notdir $(SRCS:.c=.o)))

TARGET = inputHandler

all: $(TARGET)

# Link the final binary
$(TARGET): $(OBJS)
	$(CC) -o $@ $^ $(LDFLAGS)

# for filenames under the .o extension, gracefully swap into the build dir, compile based on the .c files
build/%.o:
	@mkdir -p build
	$(CC) $(CFLAGS) -c $(shell find . -name "$*.c") -o $@

try: $(TARGET)
	./$(TARGET) 6815923762915875509 nearest ocean 0 0 3 200


# Testing compilation
TEST_SRCS = tests/nearestBiome/test_nearestB.c tests/dependencies/unity.c
TEST_OBJS = build/inputHandler.o build/nearestBiome.o build/utilityFns.o
TEST_BIN = seedInfo_tests

# Rule to build the test binary
$(TEST_BIN): $(TEST_SRCS) $(TEST_OBJS)
	$(CC) -o $@ $^ $(CFLAGS) $(LDFLAGS) -I./tests

test: $(TEST_BIN)
	./$(TEST_BIN)


clean:
	rm -rf */*.o */*.a build/*

cleanExec: clean
	rm -f $(TARGET)

cleanTest:
	rm -f $(TEST_BIN) tests/**/*.o

# file labels
.PHONY: all test clean cleanAll cleanTest try help

help:
	@echo "Available make commands:"
	@grep -E '^[a-zA-Z_-]+:([^=]|$$)' Makefile | grep -v '^\.' | awk -F':' '{print "  - " $$1}'