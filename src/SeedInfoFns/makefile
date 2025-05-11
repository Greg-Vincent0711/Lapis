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
	./$(TARGET) nearest Village 0 0 3

clean:
	rm -rf */*.o */*.a build/*

cleanExec: clean
	rm -f $(TARGET)

.PHONY: all clean cleanAll try help

help:
	@echo "Available make commands:"
	@grep -E '^[a-zA-Z_-]+:([^=]|$$)' Makefile | grep -v '^\.' | awk -F':' '{print "  - " $$1}'
