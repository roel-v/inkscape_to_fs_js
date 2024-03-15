import inkex
import inkex.paths
from inkex import TextElement, PathElement

import re

class Point():
    def __init__(self, x, y):
        self.x = round(float(x))
        self.y = round(float(y))

def clean_name(string):
    return re.sub(r'\W|^(?=\d)', '_', string)

class ToFreesewingJS(inkex.extensions.OutputExtension):
    def add_arguments(self, pars):
        pars.add_argument("--tab", type=str, dest="what")
        pars.add_argument("--fp_precision", type=int, default=4)
        pars.add_argument("--show_debug_comments", type=inkex.Boolean)

    def get_curve_point_names(self, id, point_counter):
        ep_name = self.get_point_name(id, point_counter) + "_ep"
        cp1_name = self.get_point_name(id, point_counter) + "_cp1"
        cp2_name = self.get_point_name(id, point_counter) + "_cp2"

        return (ep_name, cp1_name, cp2_name)

    def get_point_name(self, id, point_counter):
        return clean_name(f"{id}_p{point_counter}")

    def format_coordinate_value(self, coord):
        fp = self.options.fp_precision

        # Format the number with the desired precision
        formatted_value = f"{coord:.{fp}f}"
        # Split the formatted value into the integer and decimal parts
        int_part, dec_part = formatted_value.split('.')
        # Remove trailing zeros from the decimal part
        dec_part = dec_part.rstrip('0')
        # Combine the parts back, omitting the decimal part if it's empty
        final_value = int_part if dec_part == '' else f"{int_part}.{dec_part}"

        return final_value

    def path_to_code(self, id: str, path: inkex.paths.PathCommand):
        """
        This function makes JS code that defines a list of points, and then a Path that combines those points.
        """
        points_code = f"// Path: {id}\n"
        path_code = f"paths.{id} = new Path()"

        point_counter = 1

        # For a simple path with three endpoints, str(command) looks like:
        # m 42.6289 138.544
        # c 26.9235 -17.6685 28.0984 36.3167 48.7989 39.8244
        # c 22.6554 3.83889 64.7847 -23.5581 64.7847 -23.5581

        current_pen_position = Point(0, 0)

        add_debug_cmts = self.options.show_debug_comments == True

        for command in path:
            #self.msg(f"1: {command.__class__}")
            #self.msg(f"2: {command.__class__.__name__}")
            # command is a subclass of type inkex.paths.PathCommand
            # See https://inkscape.gitlab.io/inkscape/doxygen-extensions/paths_8py_source.html .

            if isinstance(command, inkex.paths.move):
                # Relative move
                #  str(command) = "m 42.6289 138.544"

                point_name = self.get_point_name(id, point_counter)
                point_counter += 1

                mt_x = self.format_coordinate_value(current_pen_position.x + command.dx)
                mt_y = self.format_coordinate_value(current_pen_position.y + command.dy)

                if add_debug_cmts:
                    points_code += f"// {str(command)}\n"
                points_code += f"points.{point_name} = new Point({mt_x}, {mt_y})\n"

                if add_debug_cmts:
                    path_code += f"\n    // inkex.paths.move: {str(command)}"
                path_code += f"\n    .move(points.{point_name})"

                current_pen_position = Point(mt_x, mt_y)
            if isinstance(command, inkex.paths.Move):
                # Absolute move
                #  str(command) = "M 42.6289 138.544"

                point_name = self.get_point_name(id, point_counter)
                point_counter += 1

                mt_x = self.format_coordinate_value(command.x)
                mt_y = self.format_coordinate_value(command.y)

                if add_debug_cmts:
                    points_code += f"// {str(command)}\n"
                points_code += f"points.{point_name} = new Point({mt_x}, {mt_y})\n"

                if add_debug_cmts:
                    path_code += f"\n    // inkex.paths.Move: {str(command)}"
                path_code += f"\n    .move(points.{point_name})"

                current_pen_position = Point(mt_x, mt_y)
            elif isinstance(command, inkex.paths.curve):
                # Relative Bezier curve
                # If we get here, the curve is a 'c' in SVG so using relative control point coordinates. This
                # corresponds to the inkex.paths.curve class, 'curve' with a lowercase 'c'.

                ep_name, cp1_name, cp2_name = self.get_curve_point_names(id, point_counter)

                point_counter += 1

                cp1_x = self.format_coordinate_value(current_pen_position.x + command.dx2)
                cp1_y = self.format_coordinate_value(current_pen_position.y + command.dy2)
                cp2_x = self.format_coordinate_value(current_pen_position.x + command.dx3)
                cp2_y = self.format_coordinate_value(current_pen_position.y + command.dy3)
                ep_x = self.format_coordinate_value(current_pen_position.x + command.dx4)
                ep_y = self.format_coordinate_value(current_pen_position.y + command.dy4)

                # Control points are relative but in FS always absolute, so we need to convert.
                if add_debug_cmts:
                    points_code += f"// {str(command)}\n"
                points_code += f"points.{cp1_name} = new Point({cp1_x}, {cp1_y})\n"
                points_code += f"points.{cp2_name} = new Point({cp2_x}, {cp2_y})\n"
                points_code += f"points.{ep_name} = new Point({ep_x}, {ep_y})\n"

                # We can safely chain here, because there's always an m or M before this.
                if add_debug_cmts:
                    path_code += f"\n    // inkex.paths.curve: {str(command)}"
                path_code += f"\n    .curve("
                path_code += f"\n        points.{cp1_name},"
                path_code += f"\n        points.{cp2_name},"
                path_code += f"\n        points.{ep_name}"
                path_code += f"\n    )"

                current_pen_position = Point(ep_x, ep_y)
            elif isinstance(command, inkex.paths.Curve):
                # Absolute Bezier curve
                # If we get here, the curve is a 'C' in SVG so using absolute control point coordinates. This
                # corresponds to the inkex.paths.Curve class, 'Curve' with a uppercase 'C'.

                ep_name, cp1_name, cp2_name = self.get_curve_point_names(id, point_counter)

                point_counter += 1

                cp1_x = self.format_coordinate_value(command.x2)
                cp1_y = self.format_coordinate_value(command.y2)
                cp2_x = self.format_coordinate_value(command.x3)
                cp2_y = self.format_coordinate_value(command.y3)
                ep_x = self.format_coordinate_value(command.x4)
                ep_y = self.format_coordinate_value(command.y4)

                if add_debug_cmts:
                    points_code += f"// {str(command)}\n"
                points_code += f"points.{cp1_name} = new Point({cp1_x}, {cp1_y})\n"
                points_code += f"points.{cp2_name} = new Point({cp2_x}, {cp2_y})\n"
                points_code += f"points.{ep_name} = new Point({ep_x}, {ep_y})\n"

                # We can safely chain here, because there's always an m or M before this.
                if add_debug_cmts:
                    path_code += f"\n    // inkex.paths.Curve: {str(command)}"
                path_code += f"\n    .curve("
                path_code += f"\n        points.{cp1_name},"
                path_code += f"\n        points.{cp2_name},"
                path_code += f"\n        points.{ep_name}"
                path_code += f"\n    )"

                current_pen_position = Point(ep_x, ep_y)

        return points_code, path_code

    def line_to_code(self, id: str, line: inkex.paths.PathCommand):
        #paths.rect = new Path()
        #    .move(points.topLeft)
        #    .line(points.bottomLeft)
        #    .line(points.bottomRight)
        #    .line(points.topRight)
        #    .line(points.topLeft)
        #    .close()
        pass

    def save(self, stream):
        # Initialize a list to hold the IDs of line and path elements
        result_code = ""

        # Get the root element of the SVG document
        root = self.document.getroot()

        # Find all <defs> elements and store their ids in a set for quick lookup
        defs_ids = {element.get_id() for element in root.findall('.//defs', root.nsmap)}

        # Iterate over all elements in the SVG
        for element in root.iter():
            # Skip elements that are children of <defs>
            if any(ancestor.get_id() in defs_ids for ancestor in element.iterancestors()):
                continue

            # Check if the element is a line or a path (Bézier curves included)
            if isinstance(element, (inkex.PathElement, inkex.Line)):
                if isinstance(element, inkex.PathElement):
                    path = inkex.paths.Path(element.get('d'))
                    points_code, path_code = self.path_to_code(element.get_id(), path)
                    result_code += f"{points_code}\n{path_code}\n"

                if isinstance(element, inkex.Line):
                    self.msg(f"@todo {inkex.Line}")
                    pass

        stream.write(result_code.encode('utf-8'))

if __name__ == '__main__':
    ToFreesewingJS().run()
