# Lapis

A Minecraft bot built around AWS Microservices and Minecraft-based tooling (lookup Cubitect and the Cubiomes Library).

Lapis has an [entire website](https://github.com/Greg-Vincent0711/Lapis-Site) (currently in the works) dedicated to its inner workings and all the stats for fellow nerds. But generally, Lapis is meant to resolve a couple small annoyances I had while enduring my annual two week Minecraft phase. Namely, having a consistent place to store coordinates that wasn't my camera roll, only to then have to manually delete a bunch of screenshots later.

You can think of Lapis as the younger, more complex sibling to [this](https://github.com/Greg-Vincent0711/Multi-purpose-Bot-for-Python/blob/main/DIscordBotVer%231.py) earlier project I made with a friend.

## Building the C Code

If someone wants to use the C code I wrote together with Cubiomes:

To use the lib and compile programs:
1. `cd` into `external/cubiomes`
2. Run `make`
3. `cd ../../SeedInfoFns`
4. Run `make`
