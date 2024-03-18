function draft_{{ path_fs_name }}(
  Path,
  Point,
  paths,
  points,
  measurements,
  options,
  utils,
  macro,
  part,
)
{
{{ points_code | indent }}
{{ path_code | indent }}
}

export { draft_{{ path_fs_name }} }
