# Compiler
CC = gcc

# Cubiomes shared lib location (relative from project root)
CUBIOMES_DIR = external/cubiomes
CUBIOMES_SO = $(CUBIOMES_DIR)/libcubiomes.so

# Compiler flags
CFLAGS = -fwrapv -fPIC -I$(CUBIOMES_DIR) -Isrc/SeedInfoFns \
         -Isrc/SeedInfoFns/nearestBiome \
         -Isrc/SeedInfoFns/nearestStructure \
         -Isrc/SeedInfoFns/spawnNear \
         -Isrc/SeedInfoFns/utility

# Linker flags
LDFLAGS = -L$(CUBIOMES_DIR) -lcubiomes -lm

# Executable name
TARGET = inputHandler

# Source files (relative to root)
SRCS = src/SeedInfoFns/inputHandler.c \
       src/SeedInfoFns/nearestBiome/nearestBiome.c \
       src/SeedInfoFns/nearestStructure/nearestStructure.c \
       src/SeedInfoFns/spawnNear/spawnNear.c \
       src/SeedInfoFns/utility/utilityFns.c

# Object files
OBJS = $(SRCS:.c=.o)

# Default target
all: $(CUBIOMES_SO) $(TARGET)

# Link executable
$(TARGET): $(OBJS)
	$(CC) -o $@ $^ $(LDFLAGS)

# Compile .c to .o
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# Build shared Cubiomes lib if needed
$(CUBIOMES_SO):
	$(CC) -fPIC -shared -o $@ \
		$(CUBIOMES_DIR)/biome.c \
		$(CUBIOMES_DIR)/generator.c \
		$(CUBIOMES_DIR)/layers.c \
		$(CUBIOMES_DIR)/rng.c

# Run test
try:
	LD_LIBRARY_PATH=$(CUBIOMES_DIR) ./$(TARGET) nearest Village 43 43 1200

# Clean build files
clean:
	rm -f $(OBJS)

cleanAll: clean
	rm -f $(TARGET) $(CUBIOMES_SO)

.PHONY: all clean cleanAll try help

help:
	@echo "Available make commands:"
	@grep -E '^[a-zA-Z_-]+:([^=]|$$)' Makefile | grep -v '^\.' | awk -F':' '{print "  - " $$1}'
