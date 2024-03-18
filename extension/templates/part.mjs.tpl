import { pctBasedOn } from '@freesewing/core'

{%- for path in paths %}
import { draft_{{path.get_fs_name()}} } from './paths/draft_{{path.get_fs_name()}}.mjs'
{%- endfor %}

function draft{{ design_name | capitalize }}{{ part_name | capitalize }}({
  Path,
  Point,
  paths,
  points,
  measurements,
  options,
  utils,
  macro,
  part
}) {
{%- for path in paths %}
    draft_{{path.id}}(Path, Point, paths, points, measurements, options, utils, macro, part)
{%- endfor %}

    return part
}

export const {{ part_name }} = {
    name: '{{ design_name }}.{{ part_name }}',
    draft: draft{{ design_name | capitalize }}{{ part_name | capitalize }},

    measurements: [
        // Enter the measurements your design needs here. See https://freesewing.dev/reference/measurements .
        {%- for m in measurements %}
      '{{ m }}',
        {%- endfor %}
    ],
    options: {
        // Enter your pattern options here. Example:
        /*
        extraLength: {
            pct: 10,
            min: 5,
            max: 20,
            label: 'Extra length',
            menu: 'fit',
            ...pctBasedOn('neck')
        }
        */
        {%- for o in options %}
        {{ o }}: {
            pct: 10,
            min: 5,
            max: 20,
            label: '{{ o }}',
            menu: 'fit'
        }
        {%- endfor %}
    }
}
