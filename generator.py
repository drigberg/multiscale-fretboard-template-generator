from dataclasses import dataclass

from PIL import Image
from PIL import ImageDraw
import matplotlib.pyplot as plt
import numpy as np


FRET_FACTOR = 17.81715
PIXEL_TO_MM = 3.77953
# PIXEL_TO_MM = 1

@dataclass
class Config:
    num_strings: int
    number_of_frets: int
    long_scale_length: float
    short_scale_length: float
    neutral_fret: int
    string_spacing_at_nut: float 
    string_spacing_at_bridge: float 

@dataclass
class FretPositions:
    fret_positions: np.array
    deltas: np.array

def get_fret_positions_along_string(config: Config, scale_length: float) -> FretPositions:
    deltas = [0]
    fret_positions = [0]
    remaining_scale_length = scale_length
    for i in range(config.number_of_frets):
        delta = remaining_scale_length / FRET_FACTOR
        deltas.append(delta)
        fret_positions.append(fret_positions[-1] + delta)
        remaining_scale_length -= delta
    return FretPositions(deltas=np.array(deltas), fret_positions=np.array(fret_positions))

def get_coordinates_for_scale(config: Config, is_long_scale: bool) -> np.array:
    scale_length = config.long_scale_length if is_long_scale is True else config.short_scale_length 
    fret_positions = get_fret_positions_along_string(config, scale_length)

    num_string_spacings_from_centerline = (config.num_strings - 1) / 2
    distance_at_nut = num_string_spacings_from_centerline * config.string_spacing_at_nut
    distance_at_bridge = num_string_spacings_from_centerline * config.string_spacing_at_bridge
    max_delta = distance_at_bridge - distance_at_nut

    multiplier = 1 if is_long_scale else -1
    distances_from_centerline = [distance_at_nut * multiplier]
    for i in range(config.number_of_frets):
        distance_from_nut = fret_positions.fret_positions[i + 1]
        distances_from_centerline.append((distance_at_nut + max_delta * distance_from_nut / scale_length) * multiplier)
    
    return np.vstack((fret_positions.fret_positions, distances_from_centerline)).T

def main():
    config = Config(
        num_strings = 7,
        long_scale_length = 673.1,
        short_scale_length = 643.1,
        number_of_frets = 24,
        neutral_fret = 7,
        string_spacing_at_nut = 7.167,
        string_spacing_at_bridge = 10.5
    )
    long_scale_coordinates = get_coordinates_for_scale(
        config=config,
        is_long_scale=True
    )
    short_scale_coordinates = get_coordinates_for_scale(
        config=config,
        is_long_scale=False
    )

    short_scale_offset = long_scale_coordinates[config.neutral_fret][0] - short_scale_coordinates[config.neutral_fret][0]
    for i in range(config.number_of_frets + 1):
        short_scale_coordinates[i][0] += short_scale_offset
    
    plot_width = round(long_scale_coordinates[-1][0] * 1.2 * PIXEL_TO_MM) 
    plot_height = round(long_scale_coordinates[-1][1] * 2.5 * PIXEL_TO_MM) 

    image = Image.new('RGBA', (plot_width, plot_height), (255,255,255,255))
    draw = ImageDraw.Draw(image)

    centerline_height = plot_height * 0.5
    x_offset = plot_width * 0.1

    # Draw centerline
    draw.line(((0, centerline_height), (plot_width, centerline_height)), fill=(0, 0, 0, 125), width=1)

    # Draw strings
    draw.line((
        (
            long_scale_coordinates[0][0] * PIXEL_TO_MM + x_offset,
            long_scale_coordinates[0][1] * PIXEL_TO_MM + centerline_height
        ),
        (
            long_scale_coordinates[-1][0] * PIXEL_TO_MM + x_offset,
            long_scale_coordinates[-1][1] * PIXEL_TO_MM + centerline_height
        )),
        fill=(0, 0, 0, 125),
        width=1
    )
    draw.line((
        (
            short_scale_coordinates[0][0] * PIXEL_TO_MM + x_offset,
            short_scale_coordinates[0][1] * PIXEL_TO_MM + centerline_height
        ),
        (
            short_scale_coordinates[-1][0] * PIXEL_TO_MM + x_offset,
            short_scale_coordinates[-1][1] * PIXEL_TO_MM + centerline_height
        )),
        fill=(0, 0, 0, 125),
        width=1
    )

    # Draw frets
    for i in range(config.number_of_frets + 1):
        draw.line(
            (
                (
                    (long_scale_coordinates[i][0] * PIXEL_TO_MM + x_offset) ,
                    (long_scale_coordinates[i][1] * PIXEL_TO_MM + centerline_height) 
                ),
                (
                    (short_scale_coordinates[i][0] * PIXEL_TO_MM + x_offset),
                    (short_scale_coordinates[i][1] * PIXEL_TO_MM + centerline_height) 
                ),
            ),
            fill=(0, 0, 0, 255),
            width=1
        )

    print("Saving image...")
    plt.axis('off')
    plt.imshow(np.asarray(image), origin='lower')
    plt.gcf().set_size_inches(plot_width / PIXEL_TO_MM / 25.4, plot_height / PIXEL_TO_MM / 25.4)
    plt.savefig('output.png', dpi=200)
    print(f"Saved image to output.png (width={plot_width}, height={plot_height})")


if __name__ == '__main__':
    main()