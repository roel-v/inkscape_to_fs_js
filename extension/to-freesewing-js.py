import inkex
import inkex.paths
from inkex import TextElement, PathElement

import sys, os, re
import enum

lib_path = os.path.join(os.path.dirname(__file__), 'site-packages')
sys.path.append(lib_path)

from jinja2 import Environment, FileSystemLoader
import pyperclip

class Point():
    def __init__(self, x, y):
        self.x = round(float(x))
        self.y = round(float(y))

class Part():
    def __init__(self, name):
        self.name = name
        self.paths = []

    def get_fs_name(self):
        ''' Get filesystem name, i.e. get name in a way that is safe to use in filenames.
        '''
        return clean_name(self.name)

class Path():
    def __init__(self, path_id):
        self.id = path_id
        self.points_code = ''
        self.path_code = ''

    def get_fs_name(self):
        return clean_name(self.id)

def clean_name(string):
    return re.sub(r'\W|^(?=\d)', '_', string)

def indent_filter(s, num_spaces=4):
    indent = ' ' * num_spaces
    return '\n'.join(indent + line for line in s.split('\n'))

class FileExistsBehaviour(enum.Enum):
    KEEP_EXISTING = enum.auto()
    FORCE_OVERWRITE = enum.auto()

class ToFreesewingJS(inkex.Effect):
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
            inkex.paths.ZoneClose: self.handle_ZoneClose,
            inkex.paths.line: self.handle_line,
            inkex.paths.Line: self.handle_Line
        }

    def add_arguments(self, pars):
        pars.add_argument("--tab", type=str, dest="what")
        pars.add_argument("--output_dir", type=str)
        pars.add_argument("--export_what", type=str)
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
        pass

    def set_current_pen(self, point_name, x, y):
        self.current_pen_point = point_name
        self.current_pen_position = Point(x, y)

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

        self.set_current_pen(point_name, mt_x, mt_y)

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

        self.set_current_pen(point_name, mt_x, mt_y)

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

        self.set_current_pen(ep_name, ep_x, ep_y)

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

        self.set_current_pen(ep_name, ep_x, ep_y)

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

        self.set_current_pen(point_name, lt_x, lt_y)

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

        self.set_current_pen(point_name, lt_x, lt_y)

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

        self.set_current_pen(point_name, lt_x, lt_y)

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

        self.set_current_pen(point_name, lt_x, lt_y)

    def do_close(self, command, cmd_name):
        add_debug_cmts = self.options.show_debug_comments == True

        if add_debug_cmts:
            self.points_code += f"// {str(command)}\n"

        if add_debug_cmts:
            self.path_code += f"\n    // inkex.paths.{cmd_name}Close: {str(command)}"
        self.path_code += f"\n    .line(points.{self.start_point})"

        self.set_current_pen(self.start_point, self.start_position.x, self.start_position.y)

    def handle_zoneClose(self, command: inkex.paths.zoneClose):
        self.do_close(command, "zone")

    def handle_ZoneClose(self, command: inkex.paths.ZoneClose):
        self.do_close(command, "Zone")

    def handle_line(self, command: inkex.paths.line):
        # Relative line
        add_debug_cmts = self.options.show_debug_comments == True

        point_name = self.get_current_point_name()
        self.point_counter += 1

        lt_x = self.format_coordinate_value(self.current_pen_position.x + command.dx)
        lt_y = self.format_coordinate_value(self.current_pen_position.y + command.dy)

        if add_debug_cmts:
            self.points_code += f"// {str(command)}\n"
        self.points_code += f"points.{point_name} = new Point({lt_x}, {lt_y})\n"

        if add_debug_cmts:
            self.path_code += f"\n    // inkex.paths.line: {str(command)}"
        self.path_code += f"\n    .line(points.{point_name})"

        self.set_current_pen(point_name, lt_x, lt_y)

    def handle_Line(self, command: inkex.paths.Line):
        # Absolute line
        add_debug_cmts = self.options.show_debug_comments == True

        point_name = self.get_current_point_name()
        self.point_counter += 1

        lt_x = self.format_coordinate_value(command.x)
        lt_y = self.format_coordinate_value(command.y)

        if add_debug_cmts:
            self.points_code += f"// {str(command)}\n"
        self.points_code += f"points.{point_name} = new Point({lt_x}, {lt_y})\n"

        if add_debug_cmts:
            self.path_code += f"\n    // inkex.paths.Line: {str(command)}"
        self.path_code += f"\n    .line(points.{point_name})"

        self.set_current_pen(point_name, lt_x, lt_y)

    def path_to_code(self, path: inkex.paths.PathCommand):
        """
        This function makes JS code that defines a list of points, and then a Path that combines those points.
        It only returns True or False for success or failure. The actual results are stored in self.points_code
        and self.path_code.
        Along the way it keeps state in various member variables, too.
        """
        self.point_counter = 1
        self.current_pen_position = Point(0, 0)

        self.points_code = f"// Path: {self.current_element_id}\n"
        self.path_code = "paths." + clean_name(self.current_element_id) + " = new Path()"

        first_command = True
        for command in path:
            #self.msg(f"1: {command.__class__}")
            #self.msg(f"2: {command.__class__.__name__}")
            # command is a subclass of type inkex.paths.PathCommand
            # See https://inkscape.gitlab.io/inkscape/doxygen-extensions/paths_8py_source.html .

            handler = self.dispatch_table.get(type(command), self.default_handler)
            handler(command)

            if first_command:
                first_command = False
                self.start_point = self.current_pen_point
                self.start_position = self.current_pen_position

        return True

    def render_template(self, template_name: str, output_filename: str, force_overwrite: FileExistsBehaviour, data: dict):
        if os.path.isfile(output_filename) and force_overwrite == False:
            return

        template_dir = 'templates'
        env = Environment(loader=FileSystemLoader(template_dir))
        env.filters['indent'] = indent_filter
        tpl = env.get_template(template_name)
        rendered_output = tpl.render(data)
        with open(output_filename, 'w') as file:
            file.write(rendered_output)

    def extract_text(self, text_element):
        # Start with the text directly in the <text> element, if any
        combined_text = (text_element.text or "").strip()

        # Add the text from any <tspan> children, if they exist
        for tspan in text_element.findall('{http://www.w3.org/2000/svg}tspan'):
            combined_text += (tspan.text or "").strip()

        # Also consider any tail text following <tspan> elements
        for tspan in text_element.getchildren():
            if tspan.tail is not None:
                combined_text += tspan.tail.strip()

        return combined_text

    def write_results(self, design_name, parts):
        output_dir = self.options.output_dir

        os.makedirs(f"{output_dir}", exist_ok=True)
        os.makedirs(f"{output_dir}\\src", exist_ok=True)
        os.makedirs(f"{output_dir}\\i18n", exist_ok=True)
        os.makedirs(f"{output_dir}\\src\\parts", exist_ok=True)

        # index.mjs, the design itself which ties together the parts. Only when it doesn't exist already.
        self.render_template('index.mjs.tpl', os.path.join(output_dir, "src", "index.mjs"), FileExistsBehaviour.KEEP_EXISTING,
            {
                'design_name' : design_name,
                'parts': parts
            }
        )

        # All individual parts. Only when they don't exist already.
        for part in parts:
            part_fs_name = part.get_fs_name()
            os.makedirs(os.path.join(output_dir, "src", "parts", part_fs_name), exist_ok=True)

            # The part definition
            self.render_template('part.mjs.tpl', os.path.join(output_dir, "src",  "parts", part_fs_name, f"{part_fs_name}.mjs"), FileExistsBehaviour.KEEP_EXISTING,
                {
                    'design_name' : design_name,
                    'part_name' : part.name,
                    'paths' : part.paths,
                }
            )

            # The individual path code fragments. Overwrite.
            for path in part.paths:
                path_fs_name = path.get_fs_name()
                os.makedirs(os.path.join(output_dir, "src", "parts", part_fs_name, "paths"), exist_ok=True)

                self.render_template('path.mjs.tpl', os.path.join(output_dir, "src", "parts", part_fs_name, "paths", f"draft_{path_fs_name}.mjs"), FileExistsBehaviour.FORCE_OVERWRITE,
                    {
                        'path_fs_name' : path_fs_name,
                        'points_code' : path.points_code,
                        'path_code' :  path.path_code,
                    }
                )

        return True

    def parse_metadata(self, root):
        metadata_layer = root.xpath('//svg:g[@inkscape:groupmode="layer" and @inkscape:label="metadata"]', namespaces=inkex.NSS)
        # @todo Use name of document as default
        design_name = "newDesign"
        if len(metadata_layer) > 0:
            name_elements = metadata_layer[0].xpath('//svg:text[@inkscape:label="design-name"]', namespaces=inkex.NSS)

            if len(name_elements) > 0:
                design_name = self.extract_text(name_elements[0])
            else:
                self.msg("No text element with label 'design-name' found in layer 'metadata', using default design name of 'newDesign'.")
        else:
            self.msg("No layer 'metadata' found in which to look for a text element with label 'design-name', using default design name of 'newDesign'.")

        return (design_name,)

    def extract_paths(self, root_element):
        # Looks for 'paths' inside the give root_element.
        # Processes all known inkex.paths types, plus Line. But all known types are derived from inkex.PathElement. We
        # process that manually now, maybe it's more elegant to also do that through the visitor pattern implemented
        # through self.dispatch_table? Might get tricky because of the inheritance. Should check how isinstance() works
        # exactly, how it deals with types that have the same parent up graph.
        types_from_table = tuple(self.dispatch_table.keys())
        other_types = (inkex.PathElement, inkex.Line, inkex.Rectangle)
        types = types_from_table + other_types

        paths = [] # return value

        for element in root_element.iter():
            if isinstance(element, types):
                if isinstance(element, inkex.PathElement):
                    path = inkex.paths.Path(element.get('d'))
                    self.current_element_id = element.get_id()
                    if not self.path_to_code(path):
                        self.msg("path_to_code failed. Unsure what to do. Probably critical bug.")
                        continue

                    new_path = Path(self.current_element_id)
                    new_path.points_code = self.points_code
                    new_path.path_code = self.path_code

                    paths.append(new_path)

                #if isinstance(element, inkex.Line):
                #    self.msg(f"@todo {inkex.Line}")
                #    pass

                #if isinstance(element, inkex.Rectangle):
                #    self.msg(f"@todo {inkex.Rectangle}")
                #    pass

        return paths

    def extract_parts(self, design_name, root):
        # Extract all FS parts, which are layers (<g> element with inkscape:groupmode="layer" attribute) and need to
        # have inkscape:label="part: front" attributes, the values of which need to start with 'part:'.
        parts = [] # return value
        svg_layers = root.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS)
        for layer in svg_layers:
            label_attrib_name = f"{{{layer.nsmap['inkscape']}}}label"
            if label_attrib_name not in layer.attrib:
                continue

            layer_label = layer.attrib[label_attrib_name]
            str_parts = re.split(r'(?i)part:', layer_label, maxsplit=1)
            if len(str_parts) <= 1:
                continue
            part_name = str_parts[1].strip()
            #self.msg(f"Found Freeswing part layer with name {part_name}")

            new_part = Part(part_name)
            new_part.paths = self.extract_paths(layer)
            parts.append(new_part)

        return parts

    def extract_code_for_selection(self, root):
        selection = self.svg.selection
        points_code = ""
        path_code = ""

        for element_id, element in selection.items():
            paths = self.extract_paths(element)
            for path in paths:
                points_code += f"{path.points_code}\n"
                path_code += f"{path.path_code}\n"

        return f"{points_code}\n{path_code}\n"

    def to_clipboard(self, path_code):
        pyperclip.copy(path_code)

    def effect(self):
        # Get the root element of the SVG document - type xml.etree.ElementTree.ElementTree
        root = self.document.getroot()

        # Get metadata, if there is any.

        design_name, *placeholder = self.parse_metadata(root)

        # What to do?
        if self.options.export_what == "all":
            # Derive part definitions from layer structure.
            parts = self.extract_parts(design_name, root)

            # Write out result files.
            self.write_results(design_name, parts)
        elif self.options.export_what == "selection":
            code = self.extract_code_for_selection(root)

            if code.strip() == "":
                self.msg("Nothing selected or selected objects aren't paths that can be converted to code.")
            else:
                self.to_clipboard(code)

if __name__ == '__main__':
    ToFreesewingJS().run()
