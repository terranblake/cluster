# This config variable is loaded into the upstream Minecraft Overviewer project,
# so it contains undefined variables.
# pylint: disable=undefined-variable

import os


def playerIcons(poi):
    if poi['id'] == 'Player':
        poi['icon'] = "https://overviewer.org/avatar/{}".format(poi['EntityId'])
        return "Last known location for {}".format(poi['EntityId'])


# Only render the signs with the filter string in them. If filter string is
# blank or unset, render all signs. Lines are joined with a configurable string.
def signFilter(poi):
    # Because of how Overviewer reads this file, we must "import os" again here.
    import os
    # Only render signs with this function
    if poi['id'] in ['Sign', 'minecraft:sign']:
        sign_filter = os.environ['RENDER_SIGNS_FILTER']
        hide_filter = os.environ['RENDER_SIGNS_HIDE_FILTER'] == 'true'
        # Transform the lines into an array and strip whitespace from each line.
        lines = list(map(lambda l: l.strip(), [poi['Text1'], poi['Text2'], poi['Text3'], poi['Text4']]))
        # Remove all leading and trailing empty lines
        while lines and not lines[0]:
            del lines[0]
        while lines and not lines[-1]:
            del lines[-1]
        # Determine if we should render this sign
        render_all_signs = len(sign_filter) == 0
        render_this_sign = sign_filter in lines
        if render_all_signs or render_this_sign:
            # If the user wants to strip the filter string, we do that here. Only
            # do this if sign_filter isn't blank.
            if hide_filter and not render_all_signs:
                lines = list(filter(lambda l: l != sign_filter, lines))
            return os.environ['RENDER_SIGNS_JOINER'].join(lines)


# returns a tuple of (xmin, zmin, xmax, zmax) using the
# crop environment variable as the total distance between
# min and max for both dimensions
def getRenderCropping(center):
    import os
    crop = int(os.getenv('FROM_CENTER', '300'))

    return (
        center[0] - crop,
        center[2] - crop,
        center[0] + crop,
        center[2] + crop
    )


worlds['minecraft'] = os.getenv("MAP_DIRECTORY", "/data/world")
outputdir = os.getenv("OUTPUT_DIRECTORY", "/data/overviewer")
texturepath = os.getenv("TEXTURES_DIRECTORY", "/minecraft-texture-pack-v1.16")
center = [int(x) for x in os.getenv('CENTER', '0,64,0').split(',')]

markers = [
    dict(name="Players", filterFunction=playerIcons, createInfoWindow=True, showIconInLegend=True)
    # dict(name="Signs", filterFunction=signFilter)
]

cave_rendermode = [Base(), Depth(min=0, max=64), Cave(only_lit=True), MineralOverlay(minerals=[(27, (255, 234, 0)), (28, (255, 234, 0)), (66, (255, 234, 0))]), EdgeLines()]

# renders["day-normal-north"] = {
#     'world': 'minecraft',
#     'title': 'Normal north',
#     'rendermode': "smooth_lighting",
#     "dimension": "overworld",
#     'markers': markers,
#     "northdirection" : "lower-right",
#     "crop": getRenderCropping(center)
# }

renders["day-normal-west"] = {
    'world': 'minecraft',
    'title': 'Normal west',
    'rendermode': "smooth_lighting",
    "dimension": "overworld",
    'markers': markers,
    "northdirection" : "upper-right",
    "crop": getRenderCropping(center)
}

# renders["day-caves-north"] = {
#     'world': 'minecraft',
#     'title': 'Caves north',
#     'rendermode': cave_rendermode,
#     "dimension": "overworld",
#     'markers': markers,
#     "northdirection" : "lower-right",
#     "crop": getRenderCropping(center)
# }

cave_rendermode = [ClearBase(), Depth(min=0, max=16), MineralOverlay(minerals=[(56, (255, 0, 255)), (57, (255, 0, 255))]), EdgeLines()]
renders["day-caves-west-0-16-diamonds"] = {
    'world': 'minecraft',
    'title': 'Caves 0-16 diamonds west',
    'rendermode': cave_rendermode,
    "dimension": "overworld",
    'markers': markers,
    "northdirection" : "upper-right",
    "crop": getRenderCropping(center)
}

cave_rendermode = [Base(), Depth(min=0, max=12), Cave(only_lit=True), MineralOverlay(minerals=[(27, (255, 234, 0)), (28, (255, 234, 0)), (66, (255, 234, 0))]), EdgeLines()]
renders["day-caves-west-0-12"] = {
    'world': 'minecraft',
    'title': 'Caves 0-12 west',
    'rendermode': cave_rendermode,
    "dimension": "overworld",
    'markers': markers,
    "northdirection" : "upper-right",
    "crop": getRenderCropping(center)
}

cave_rendermode = [Base(), Depth(min=13, max=24), Cave(only_lit=True), MineralOverlay(minerals=[(27, (255, 234, 0)), (28, (255, 234, 0)), (66, (255, 234, 0))]), EdgeLines()]
renders["day-caves-west-13-24"] = {
    'world': 'minecraft',
    'title': 'Caves 13-24 west',
    'rendermode': cave_rendermode,
    "dimension": "overworld",
    'markers': markers,
    "northdirection" : "upper-right",
    "crop": getRenderCropping(center)
}

cave_rendermode = [Base(), Depth(min=25, max=36), Cave(only_lit=True), MineralOverlay(minerals=[(27, (255, 234, 0)), (28, (255, 234, 0)), (66, (255, 234, 0))]), EdgeLines()]
renders["day-caves-west-25-36"] = {
    'world': 'minecraft',
    'title': 'Caves 25-36 west',
    'rendermode': cave_rendermode,
    "dimension": "overworld",
    'markers': markers,
    "northdirection" : "upper-right",
    "crop": getRenderCropping(center)
}

cave_rendermode = [Base(), Depth(min=37, max=48), Cave(only_lit=True), MineralOverlay(minerals=[(27, (255, 234, 0)), (28, (255, 234, 0)), (66, (255, 234, 0))]), EdgeLines()]
renders["day-caves-west-37-48"] = {
    'world': 'minecraft',
    'title': 'Caves 37-48 west',
    'rendermode': cave_rendermode,
    "dimension": "overworld",
    'markers': markers,
    "northdirection" : "upper-right",
    "crop": getRenderCropping(center)
}

cave_rendermode = [Base(), Depth(min=49, max=64), Cave(only_lit=True), MineralOverlay(minerals=[(27, (255, 234, 0)), (28, (255, 234, 0)), (66, (255, 234, 0))]), EdgeLines()]
renders["day-caves-west-49-64"] = {
    'world': 'minecraft',
    'title': 'Caves 49-64 west',
    'rendermode': cave_rendermode,
    "dimension": "overworld",
    'markers': markers,
    "northdirection" : "upper-right",
    "crop": getRenderCropping(center)
}

# renders["day-west"] = {
#     'world': 'minecraft',
#     'title': 'West',
#     'rendermode': 'smooth_lighting',
#     "dimension": "overworld",
#     'markers': markers,
#     "northdirection" : "upper-right",
#     "crop": getRenderCropping(center)
# }

# renders["day-east"] = {
#     'world': 'minecraft',
#     'title': 'West',
#     'rendermode': 'smooth_lighting',
#     "dimension": "overworld",
#     'markers': markers,
#     "northdirection" : "lower-left",
#     "crop": getRenderCropping(center)
# }

# renders["night"] = {
#     'world': 'minecraft',
#     'title': 'Night',
#     'rendermode': 'smooth_night',
#     "dimension": "overworld",
#     'markers': markers
# }

renders["nether"] = {
    "world": "minecraft",
    "title": "Nether",
    "rendermode": 'nether_smooth_lighting',
    "dimension": "nether",
    'markers': markers,
    "crop": getRenderCropping(center)
}

renders["end"] = {
    "world": "minecraft",
    "title": "End",
    "rendermode": [Base(), EdgeLines(), SmoothLighting(strength=0.5)],
    "dimension": "end",
    'markers': markers,
    "crop": getRenderCropping(center)
}

# renders["day-north-biomes"] = {
#     'world': 'minecraft',
#     'rendermode': [ClearBase(), BiomeOverlay()],
#     'title': "Biome Coloring Overlay",
#     "dimension": "overworld",
#     "northdirection" : "lower-right",
#     'overlay': ["day-normal-north"],
#     "crop": getRenderCropping(center)
# }

# renders["overlay_mobs"] = {
#     'world': 'minecraft',
#     'rendermode': [ClearBase(), SpawnOverlay()],
#     'title': "Mob Spawnable Areas Overlay",
#     "dimension": "overworld",
#     'overlay': ["day"]
# }

# renders["overlay_slime"] = {
#     'world': 'minecraft',
#     'rendermode': [ClearBase(), SlimeOverlay()],
#     'title': "Slime Chunk Overlay",
#     "dimension": "overworld",
#     'overlay': ["day"]
# }