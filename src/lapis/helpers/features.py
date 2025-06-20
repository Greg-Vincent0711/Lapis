STRUCTURES = [
    "Desert Pyramid",
    "Jungle Temple",
    "Jungle Pyramid",
    "Swamp Hut",
    "Igloo",
    "Village",
    "Ocean Ruin",
    "Shipwreck",
    "Monument",
    "Mansion",
    "Outpost",
    "Ruined Portal",
    "Ruined Portal_N",
    "Ancient City",
    "Treasure",
    "Mineshaft",
    "Desert Well",
    "Geode",
    "Trail Ruins",
    "Trial Chambers",
]


BIOMES = [
    "Ocean",
    "Plains",
    "Desert",
    "Mountains",
    "Extreme Hills",
    "Forest",
    "Taiga",
    "Swamp",
    "Swampland",
    "River",
    "Frozen Ocean",
    "Frozen River",
    "Snowy Tundra",
    "Snowy Mountains",
    "Mushroom Fields",
    "Mushroom Field Shore",
    "Beach",
    "Desert Hills",
    "Wooded Hills",
    "Taiga Hills",
    "Mountain Edge",
    "Jungle",
    "Jungle Hills",
    "Jungle Edge",
    "Deep Ocean",
    "Stone Shore",
    "Snowy Beach",
    "Birch Forest",
    "Birch Forest Hills",
    "Dark Forest",
    "Snowy Taiga",
    "Snowy Taiga Hills",
    "Giant Tree Taiga",
    "Giant Tree Taiga Hills",
    "Wooded Mountains",
    "Savanna",
    "Savanna Plateau",
    "Badlands",
    "Wooded Badlands Plateau",
    "Badlands Plateau",
    "Small End Islands",
    "End Midlands",
    "End Highlands",
    "End Barrens",
    "Warm Ocean",
    "Lukewarm Ocean",
    "Cold Ocean",
    "Deep Warm Ocean",
    "Deep Lukewarm Ocean",
    "Deep Cold Ocean",
    "Deep Frozen Ocean",
    "Seasonal Forest",
    "Rainforest",
    "Shrubland",
    "Sunflower Plains",
    "Desert Lakes",
    "Gravelly Mountains",
    "Flower Forest",
    "Taiga Mountains",
    "Swamp Hills",
    "Ice Spikes",
    "Modified Jungle",
    "Modified Jungle Edge",
    "Tall Birch Forest",
    "Tall Birch Hills",
    "Dark Forest Hills",
    "Snowy Taiga Mountains",
    "Giant Spruce Taiga",
    "Giant Spruce Taiga Hills",
    "Modified Gravelly Mountains",
    "Shattered Savanna",
    "Shattered Savanna Plateau",
    "Eroded Badlands",
    "Modified Wooded Badlands Plateau",
    "Modified Badlands Plateau",
    "Bamboo Jungle",
    "Bamboo Jungle Hills",
    "Dripstone Caves",
    "Lush Caves",
    "Meadow",
    "Grove",
    "Snowy Slopes",
    "Jagged Peaks",
    "Frozen Peaks",
    "Stony Peaks",
    "Deep Dark",
    "Mangrove Swamp",
    "Cherry Grove",
    "Shattered Plateau",
    "Pale Garden"
]

'''
To keep things user-readable, the biomes and structures are in a regular format.
inputHandler.c and associated files work with different formats though.
So this will be changed when a user passes a feature automatically
# when passed to cubiomes - replace(" ", "-").lower()
# when passed to cubiomes - replace(" ", "-")
'''
ALL_FEATURES = STRUCTURES + BIOMES
