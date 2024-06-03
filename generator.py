from dataclasses import dataclass
from schema import Schema, And, Or
import yaml

from PIL import Image
from PIL import ImageDraw
import numpy as np

# Standard factor for determining the distance between frets 0 and 1
# Source: https://www.stewmac.com/video-and-ideas/online-resources/learn-about-guitar-and-instrument-fretting-and-fretwork/fret-scale-rule-instructions/
FRET_FACTOR = 17.817154

# The "official" conversion factor from millimeters to pixels
MM_TO_PIXEL_GLOBAL = 3.7795275595
# Factor of incorrectness when using the pixel conversion
WEIRDNESS_FACTOR = 1.3338508981906796
# Our conversion factor
MM_TO_PIXEL = MM_TO_PIXEL_GLOBAL / WEIRDNESS_FACTOR

config_schema = Schema(
    {
        'left_handed': And(bool),
        'num_strings': Or(int, float),
        'number_of_frets': Or(int, float),
        'long_scale_length': And(float),
        'short_scale_length': And(float),
        'neutral_fret': Or(int, float),
        'string_spacing_at_nut': And(float),
        'string_spacing_at_bridge': And(float)
    }
)

@dataclass
class Config:
    left_handed: bool
    num_strings: int
    number_of_frets: int
    long_scale_length: float
    short_scale_length: float
    neutral_fret: int
    string_spacing_at_nut: float 
    string_spacing_at_bridge: float

@dataclass
class ExportMode:
    label: str
    as_points: bool
    draw_strings: bool = False

EXPORT_MODES = [
    ExportMode(label='lines-with-strings', as_points=False, draw_strings=True),
    ExportMode(label='lines-without-strings', as_points=False, draw_strings=False),
    ExportMode(label='only-points', as_points=True)
]

def load_config() -> Config:
    with open("config.yml") as stream:
        data = yaml.safe_load(stream)
    config_schema.validate(data)
    return Config(
        left_handed=data['left_handed'],
        num_strings=int(data['num_strings']),
        number_of_frets=int(data['number_of_frets']),
        long_scale_length=data['long_scale_length'],
        short_scale_length=data['short_scale_length'],
        neutral_fret=int(data['neutral_fret']),
        string_spacing_at_nut=data['string_spacing_at_nut'],
        string_spacing_at_bridge=data['string_spacing_at_bridge']
    )

# Finds each fret's distance from fret 0 by iteratively applying the fret factor
def get_fret_positions_along_string(config: Config, scale_length: float) -> np.array:
    fret_positions = [0]
    remaining_scale_length = scale_length
    for i in range(config.number_of_frets):
        delta = remaining_scale_length / FRET_FACTOR
        fret_positions.append(fret_positions[-1] + delta)
        remaining_scale_length -= delta
    return np.array(fret_positions)

# Pairs each fret's distance from fret 0 with its distance from the centerline
def get_coordinates_for_scale(config: Config, is_long_scale: bool) -> np.array:
    scale_length = config.long_scale_length if is_long_scale is True else config.short_scale_length 
    fret_positions = get_fret_positions_along_string(config, scale_length)

    num_string_spacings_from_centerline = (config.num_strings - 1) / 2
    distance_at_nut = num_string_spacings_from_centerline * config.string_spacing_at_nut
    distance_at_bridge = num_string_spacings_from_centerline * config.string_spacing_at_bridge
    max_delta = distance_at_bridge - distance_at_nut

    # draw long scale above centerline
    multiplier = -1 if is_long_scale else 1
    distances_from_centerline = [distance_at_nut * multiplier]
    for i in range(config.number_of_frets):
        distance_from_nut = fret_positions[i + 1]
        distances_from_centerline.append((distance_at_nut + max_delta * distance_from_nut / scale_length) * multiplier)
    
    return np.vstack((fret_positions, distances_from_centerline)).T

def main():
    config = load_config()

    # Get all fret coordinates
    long_scale_coords = get_coordinates_for_scale(
        config=config,
        is_long_scale=True
    )
    short_scale_coords = get_coordinates_for_scale(
        config=config,
        is_long_scale=False
    )

    # Align to neutral fret
    short_scale_offset = long_scale_coords[config.neutral_fret][0] - short_scale_coords[config.neutral_fret][0]
    for i in range(config.number_of_frets + 1):
        short_scale_coords[i][0] += short_scale_offset
    
    # Get plot dimensions
    plot_width = abs(round(long_scale_coords[-1][0] * 1.2 * MM_TO_PIXEL))
    plot_height = abs(round(long_scale_coords[-1][1] * 3 * MM_TO_PIXEL))
    centerline_height = plot_height * 0.5
    x_offset = plot_width * 0.1

    for export_mode in EXPORT_MODES:
        # Init image
        image = Image.new('RGBA', (plot_width, plot_height), (255,255,255,255))
        draw = ImageDraw.Draw(image)

        # Draw centerline
        draw.line(((0, centerline_height), (plot_width, centerline_height)), fill=(0, 0, 0, 255), width=1)
        
        def get_xy(coords: np.array) -> tuple[float]:
            x = coords[0] * MM_TO_PIXEL + x_offset
            if not config.left_handed: 
                x = plot_width - x
            y = coords[1] * MM_TO_PIXEL + centerline_height
            return (x, y)

        # Draw strings
        if export_mode.draw_strings:
            for scale_coordinates in [long_scale_coords, short_scale_coords]:
                draw.line((get_xy(scale_coordinates[0]), get_xy(scale_coordinates[-1])), fill=(0, 0, 0, 255), width=1)

        # Draw frets
        for i in range(config.number_of_frets + 1): 
            long_scale_xy = get_xy(long_scale_coords[i])
            short_scale_xy = get_xy(short_scale_coords[i])            
            if export_mode.as_points:
                draw.point(long_scale_xy, fill=(0, 0, 0, 255))
                draw.point(short_scale_xy, fill=(0, 0, 0, 255))  
            else:
                draw.line((long_scale_xy, short_scale_xy), fill=(0, 0, 0, 255), width=1)

        # Export
        print("Saving image...")
        filename = f"output/{export_mode.label}.png"
        image.save(filename, "PNG")
        print(f"Saved image to {filename} ({image.width}x{image.height})")

if __name__ == '__main__':
    main()