from svg_export import export_delaunay_svg
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--export_svg', action='store_true', help='Export results to SVG')
parser.add_argument('--svg_filename', type=str, default='output.svg', help='SVG output filename')
args = parser.parse_args()

# After generating Delaunay triangles:
# points = ... (your input points)
# delaunay = scipy.spatial.Delaunay(points)
# triangles = [tuple(points[simplex]) for simplex in delaunay.simplices]

if args.export_svg:
    export_delaunay_svg(triangles, args.svg_filename, metadata={"creator": "Cubist Art Generator"})