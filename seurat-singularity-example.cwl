cwlVersion: v1.0
class: CommandLineTool
requirements:
  DockerRequirement:
    dockerImageId: {host_directory}/crescent-seurat_3.1.4-3.6.3-3.10.sif
    dockerPull: crescentdev/crescent-seurat:3.1.4-3.6.3-3.10
baseCommand: [Rscript]
arguments:
  - position: 0
    valueFrom: $(inputs.R_dir.dirname)/$(inputs.R_dir.basename)/$(inputs.R_script.basename)
outputs:
  seurat_output:
    type: Directory
    outputBinding:
      glob: ["SEURAT/"]
inputs:
  R_dir:
    type: Directory
    default:
      class: Directory
      path: pipeline
  R_script:
    type: File
    default:
      class: File
      path: pipeline/Runs_Seurat_v3.R
  sc_input:
    type: Directory
    inputBinding:
      position: 1
      prefix: -i
    default:
      class: Directory
      path: input
  runs_cwl:
    type: string
    default: Y
    inputBinding:
      position: 19
      prefix: -w
  outs_dir:
    type: string
    default: N
    inputBinding:
      position: 20
      prefix: -o 
  sc_input_type:
    type: string
    inputBinding:
      position: 2
      prefix: -t
  resolution:
    type: float?
    inputBinding:
      position: 3
      prefix: -r
  project_id:
    type: string
    inputBinding:
      position: 5
      prefix: -p
  summary_plots:
    type: string?
    inputBinding:
      position: 6
      prefix: -s
  colour_tsne_discrete:
    type: File?
    inputBinding:
      position: 7
      prefix: -c
  list_genes:
    type: string?
    inputBinding:
      position: 8
      prefix: -g
  opacity:
    type: float?
    inputBinding:
      position: 9
      prefix: -a
  pca_dimensions:
    type: int?
    inputBinding:
      position: 10
      prefix: -d
  normalization_method:
    type: string?
    inputBinding:
      position: 11
      prefix: -b
  apply_cell_filters:
    type: string
    default: Y
    inputBinding:
      position: 12
      prefix: -f
  percent_mito:
    type: string?
    inputBinding:
      position: 13
      prefix: -m
  percent_ribo:
    type: string?
    inputBinding:
      position: 14
      prefix: -q
  number_genes:
    type: string?
    inputBinding:
      position: 15
      prefix: -n
  number_reads:
    type: string?
    inputBinding:
      position: 16
      prefix: -v
  return_threshold:
    type: float?
    inputBinding:
      position: 17
      prefix: -e
  number_cores:
    type: string?
    inputBinding:
      position: 18
      prefix: -u
