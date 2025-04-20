# c compilier option
CC = gcc

# compilier flags - add cubiomes as a header, integer overflow wrap around
CFLAGS = -I../external/cubiomes -fwrapv
# linker flags - cubiomes compiled lib, math library
LDFLAGS = ../external/cubiomes/libcubiomes.a -lm

SRCS = seedInfoFns.c seedUtility.c

# create object files
OBJS = $(SRCS:.c=.o)

# build into seedInfoFns
all: seedInfoFns
seedInfoFns: $(OBJS)
	$(CC) -o $@ $^ $(LDFLAGS)

# commands
clean:
	rm -f *.o *.a

cleanExec:
	rm seedInfoFns

tryExample:
	./seedInfoFns nearestBiome Plains 0 0 0 1024

.PHONY: help

help:
	@echo "Available make commands:"
	@grep -E '^[a-zA-Z_-]+:([^=]|$$)' Makefile | grep -v '^\.' | awk -F':' '{print "  - " $$1}'
