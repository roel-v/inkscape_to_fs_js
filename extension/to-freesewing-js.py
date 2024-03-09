import inkex
import inkex.paths
from inkex import TextElement, PathElement

class ToFreesewingJS(inkex.extensions.OutputExtension):
    def add_arguments(self, pars):
        pars.add_argument("--tab", type=str, dest="what")
        pars.add_argument("--fp_precision", type=int, default=4)
        pass

    def path_to_code(self, id: str, path: inkex.paths.PathCommand):
        """
        This function makes JS code that defines a list of points, and then a Path that combines those points.
        """
        points_code = f"# Path: {id}"
        path_code = f"paths.{id} = new Path()"

        point_counter = 1

        # For a simple path with three endpoints, str(command) looks like:
        # m 42.6289 138.544
        # c 26.9235 -17.6685 28.0984 36.3167 48.7989 39.8244
        # c 22.6554 3.83889 64.7847 -23.5581 64.7847 -23.5581

        fp = self.options.fp_precision

        for command in path:
            #self.msg(f"1: {command.__class__}")
            #self.msg(f"2: {command.__class__.__name__}")
            # command is a subclass of type inkex.paths.PathCommand
            # See https://inkscape.gitlab.io/inkscape/doxygen-extensions/paths_8py_source.html .

            if isinstance(command, inkex.paths.move):
                #  str(command) = "m 42.6289 138.544"

                point_name = f"{id}_p{point_counter}"
                point_counter += 1

                points_code += f"points.{point_name} = new Point({command.dx:.{fp}f}, {command.dy:.{fp}f})\n"

                path_code += f"\n    .move(points.{point_name})"
            elif isinstance(command, inkex.paths.curve):
                #code += f"Curve {str(command)}"

                ep_name = f"{id}_p{point_counter}_ep"
                cp1_name = f"{id}_p{point_counter}_cp1"
                cp2_name = f"{id}_p{point_counter}_cp2"
                point_counter += 1

                points_code += f"points.{ep_name} = new Point({command.dx2:.{fp}f}, {command.dy2:.{fp}f})\n"
                points_code += f"points.{cp1_name} = new Point({command.dx3:.{fp}f}, {command.dy3:.{fp}f})\n"
                points_code += f"points.{cp2_name} = new Point({command.dx4:.{fp}f}, {command.dy4:.{fp}f})\n"

                path_code += f"\n    .curve("
                path_code += f"\n        points.{ep_name},"
                path_code += f"\n        points.{cp1_name},"
                path_code += f"\n        points.{cp2_name}"
                path_code += f"\n    )"

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

        # Iterate over all elements in the SVG
        for element in self.document.getroot().iter():
            # Check if the element is a line or a path (Bézier curves included)
            if isinstance(element, (inkex.PathElement, inkex.Line)):
                if isinstance(element, inkex.PathElement):
                    path = inkex.paths.Path(element.get('d'))
                    points_code, path_code = self.path_to_code(element.get_id(), path)
                    result_code += f"{points_code}\n{path_code}\n"

                if isinstance(element, inkex.Line):
                    self.msg(f"{inkex.Line}")
                    pass

        stream.write(result_code.encode('utf-8'))

if __name__ == '__main__':
    ToFreesewingJS().run()
