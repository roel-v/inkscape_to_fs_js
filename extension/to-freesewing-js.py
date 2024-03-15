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
    def __init__(self):
        super().__init__()

        self.dispatch_table = {
            inkex.paths.move: self.handle_move,
            inkex.paths.Move: self.handle_Move,
            inkex.paths.curve: self.handle_curve,
            inkex.paths.Curve: self.handle_Curve,
            inkex.paths.horz: self.handle_horz,
            inkex.paths.Horz: self.handle_Horz,
            inkex.paths.vert: self.handle_vert,
            inkex.paths.Vert: self.handle_Vert,
            inkex.paths.zoneClose: self.handle_zoneClose,
            inkex.paths.ZoneClose: self.handle_ZoneClose
        }

    def add_arguments(self, pars):
        pars.add_argument("--tab", type=str, dest="what")
        pars.add_argument("--fp_precision", type=int, default=4)
        pars.add_argument("--show_debug_comments", type=inkex.Boolean)

    def get_current_curve_point_names(self):
        ep_name = self.get_current_point_name() + "_ep"
        cp1_name = self.get_current_point_name() + "_cp1"
        cp2_name = self.get_current_point_name() + "_cp2"

        return (ep_name, cp1_name, cp2_name)

    def get_current_point_name(self):
        return clean_name(f"{self.current_element_id}_p{self.point_counter}")

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

    def default_handler(self, value):
        self.msg(f"Unknown Inkex type: {type(value)}")

    def handle_move(self, command: inkex.paths.move):
        # Relative move
        #  str(command) = "m 42.6289 138.544"

        add_debug_cmts = self.options.show_debug_comments == True

        point_name = self.get_current_point_name()
        self.point_counter += 1

        mt_x = self.format_coordinate_value(self.current_pen_position.x + command.dx)
        mt_y = self.format_coordinate_value(self.current_pen_position.y + command.dy)

        if add_debug_cmts:
            self.points_code += f"// {str(command)}\n"
        self.points_code += f"points.{point_name} = new Point({mt_x}, {mt_y})\n"

        if add_debug_cmts:
            self.path_code += f"\n    // inkex.paths.move: {str(command)}"
        self.path_code += f"\n    .move(points.{point_name})"

        self.current_pen_position = Point(mt_x, mt_y)

    def handle_Move(self, command: inkex.paths.Move):
        # Absolute move
        #  str(command) = "M 42.6289 138.544"

        add_debug_cmts = self.options.show_debug_comments == True

        point_name = self.get_current_point_name()
        self.point_counter += 1

        mt_x = self.format_coordinate_value(command.x)
        mt_y = self.format_coordinate_value(command.y)

        if add_debug_cmts:
            self.points_code += f"// {str(command)}\n"
        self.points_code += f"points.{point_name} = new Point({mt_x}, {mt_y})\n"

        if add_debug_cmts:
            self.path_code += f"\n    // inkex.paths.Move: {str(command)}"
        self.path_code += f"\n    .move(points.{point_name})"

        self.current_pen_position = Point(mt_x, mt_y)

    def handle_curve(self, command: inkex.paths.curve):
        # Relative Bezier curve
        # If we get here, the curve is a 'c' in SVG so using relative control point coordinates. This
        # corresponds to the inkex.paths.curve class, 'curve' with a lowercase 'c'.

        add_debug_cmts = self.options.show_debug_comments == True

        ep_name, cp1_name, cp2_name = self.get_current_curve_point_names()

        self.point_counter += 1

        cp1_x = self.format_coordinate_value(self.current_pen_position.x + command.dx2)
        cp1_y = self.format_coordinate_value(self.current_pen_position.y + command.dy2)
        cp2_x = self.format_coordinate_value(self.current_pen_position.x + command.dx3)
        cp2_y = self.format_coordinate_value(self.current_pen_position.y + command.dy3)
        ep_x = self.format_coordinate_value(self.current_pen_position.x + command.dx4)
        ep_y = self.format_coordinate_value(self.current_pen_position.y + command.dy4)

        # Control points are relative but in FS always absolute, so we need to convert.
        if add_debug_cmts:
            self.points_code += f"// {str(command)}\n"
        self.points_code += f"points.{cp1_name} = new Point({cp1_x}, {cp1_y})\n"
        self.points_code += f"points.{cp2_name} = new Point({cp2_x}, {cp2_y})\n"
        self.points_code += f"points.{ep_name} = new Point({ep_x}, {ep_y})\n"

        # We can safely chain here, because there's always an m or M before this.
        if add_debug_cmts:
            self.path_code += f"\n    // inkex.paths.curve: {str(command)}"
        self.path_code += f"\n    .curve("
        self.path_code += f"\n        points.{cp1_name},"
        self.path_code += f"\n        points.{cp2_name},"
        self.path_code += f"\n        points.{ep_name}"
        self.path_code += f"\n    )"

        self.current_pen_position = Point(ep_x, ep_y)

    def handle_Curve(self, command: inkex.paths.Curve):
        # Absolute Bezier curve
        # If we get here, the curve is a 'C' in SVG so using absolute control point coordinates. This
        # corresponds to the inkex.paths.Curve class, 'Curve' with a uppercase 'C'.

        add_debug_cmts = self.options.show_debug_comments == True

        ep_name, cp1_name, cp2_name = self.get_current_curve_point_names()

        self.point_counter += 1

        cp1_x = self.format_coordinate_value(command.x2)
        cp1_y = self.format_coordinate_value(command.y2)
        cp2_x = self.format_coordinate_value(command.x3)
        cp2_y = self.format_coordinate_value(command.y3)
        ep_x = self.format_coordinate_value(command.x4)
        ep_y = self.format_coordinate_value(command.y4)

        if add_debug_cmts:
            self.points_code += f"// {str(command)}\n"
        self.points_code += f"points.{cp1_name} = new Point({cp1_x}, {cp1_y})\n"
        self.points_code += f"points.{cp2_name} = new Point({cp2_x}, {cp2_y})\n"
        self.points_code += f"points.{ep_name} = new Point({ep_x}, {ep_y})\n"

        # We can safely chain here, because there's always an m or M before this.
        if add_debug_cmts:
            self.path_code += f"\n    // inkex.paths.Curve: {str(command)}"
        self.path_code += f"\n    .curve("
        self.path_code += f"\n        points.{cp1_name},"
        self.path_code += f"\n        points.{cp2_name},"
        self.path_code += f"\n        points.{ep_name}"
        self.path_code += f"\n    )"

        self.current_pen_position = Point(ep_x, ep_y)

    def handle_horz(self, command: inkex.paths.horz):
        # Relative horizontal line
        add_debug_cmts = self.options.show_debug_comments == True

        point_name = self.get_current_point_name()
        self.point_counter += 1

        lt_x = self.format_coordinate_value(self.current_pen_position.x + command.dx)
        lt_y = self.format_coordinate_value(self.current_pen_position.y)

        if add_debug_cmts:
            self.points_code += f"// {str(command)}\n"
        self.points_code += f"points.{point_name} = new Point({lt_x}, {lt_y})\n"

        if add_debug_cmts:
            self.path_code += f"\n    // inkex.paths.horz: {str(command)}"
        self.path_code += f"\n    .line(points.{point_name})"

        self.current_pen_position = Point(lt_x, lt_y)

    def handle_Horz(self, command: inkex.paths.Horz):
        # Absolute horizontal line
        add_debug_cmts = self.options.show_debug_comments == True

        point_name = self.get_current_point_name()
        self.point_counter += 1

        lt_x = self.format_coordinate_value(command.x)
        lt_y = self.format_coordinate_value(self.current_pen_position.y)

        if add_debug_cmts:
            self.points_code += f"// {str(command)}\n"
        self.points_code += f"points.{point_name} = new Point({lt_x}, {lt_y})\n"

        if add_debug_cmts:
            self.path_code += f"\n    // inkex.paths.Horz: {str(command)}"
        self.path_code += f"\n    .line(points.{point_name})"

        self.current_pen_position = Point(lt_x, lt_y)

    def handle_vert(self, command: inkex.paths.vert):
        # Relative vertical line
        add_debug_cmts = self.options.show_debug_comments == True

        point_name = self.get_current_point_name()
        self.point_counter += 1

        lt_x = self.format_coordinate_value(self.current_pen_position.x)
        lt_y = self.format_coordinate_value(self.current_pen_position.y + command.dy)

        if add_debug_cmts:
            self.points_code += f"// {str(command)}\n"
        self.points_code += f"points.{point_name} = new Point({lt_x}, {lt_y})\n"

        if add_debug_cmts:
            self.path_code += f"\n    // inkex.paths.vert: {str(command)}"
        self.path_code += f"\n    .line(points.{point_name})"

        self.current_pen_position = Point(lt_x, lt_y)

    def handle_Vert(self, command: inkex.paths.Vert):
        # Absolute vertical line
        add_debug_cmts = self.options.show_debug_comments == True

        point_name = self.get_current_point_name()
        self.point_counter += 1

        lt_x = self.format_coordinate_value(self.current_pen_position.x)
        lt_y = self.format_coordinate_value(command.y)

        if add_debug_cmts:
            self.points_code += f"// {str(command)}\n"
        self.points_code += f"points.{point_name} = new Point({lt_x}, {lt_y})\n"

        if add_debug_cmts:
            self.path_code += f"\n    // inkex.paths.Vert: {str(command)}"
        self.path_code += f"\n    .line(points.{point_name})"

        self.current_pen_position = Point(lt_x, lt_y)

    def handle_zoneClose(self, command: inkex.paths.zoneClose):
        pass

    def handle_ZoneClose(self, command: inkex.paths.ZoneClose):
        pass

    def path_to_code(self, path: inkex.paths.PathCommand):
        """
        This function makes JS code that defines a list of points, and then a Path that combines those points.
        """

        self.point_counter = 1
        self.current_pen_position = Point(0, 0)

        self.points_code = f"// Path: {self.current_element_id}\n"
        self.path_code = "paths." + clean_name(self.current_element_id) + " = new Path()"

        for command in path:
            #self.msg(f"1: {command.__class__}")
            #self.msg(f"2: {command.__class__.__name__}")
            # command is a subclass of type inkex.paths.PathCommand
            # See https://inkscape.gitlab.io/inkscape/doxygen-extensions/paths_8py_source.html .

            handler = self.dispatch_table.get(type(command), self.default_handler)
            handler(command)

        return True

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

            # Process all known types, plus Line. But all known types are derived from inkex.PathElement. We process
            # that manually now, maybe it's more elegant to also do that through the visitor pattern implemented through
            # self.dispatch_table? Might get tricky because of the inheritance. Should check how isinstance() works
            # exactly.
            types_from_table = tuple(self.dispatch_table.keys())
            types = types_from_table + (inkex.PathElement,)

            if isinstance(element, types):
                if isinstance(element, inkex.PathElement):
                    path = inkex.paths.Path(element.get('d'))
                    self.current_element_id = element.get_id()
                    result = self.path_to_code(path)
                    result_code += f"{self.points_code}\n{self.path_code}\n"

                if isinstance(element, inkex.Line):
                    self.msg(f"@todo {inkex.Line}")
                    pass

        stream.write(result_code.encode('utf-8'))

if __name__ == '__main__':
    ToFreesewingJS().run()
