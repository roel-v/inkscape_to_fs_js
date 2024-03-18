import { Design } from '@freesewing/core'
import { i18n } from '../i18n/index.mjs'
{%- for part in parts %}
import { {{ part.name }} } from './parts/{{ part.name }}/{{ part.name }}.mjs'
{%- endfor %}

/*
 * Create the design
 */
const {{ design_name | capitalize }} = new Design({
  data: {
    name: '{{ design_name | lower }}',
    version: '0.0.1',
  },
  parts: [
{%- for part in parts %}
    {{ part.name }},
{%- endfor %}
  ]
})

export { {% for part in parts -%} {{ part.name }}{{ ", " }}{%- endfor -%} {{ design_name | capitalize }}, i18n }
