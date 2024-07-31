#!/opt/hky-venv/bin/python
# Author: 赩林, xilin0x7f@163.com
import argparse
import nibabel as nib
import numpy as np
import polars as pl
import subprocess

def usage():
    print(r'''
    Usage: python metric_report.py -i <input_file> -s <surface> [<surface_area>] -a <atlas> -t <threshold> -o <output_file>
    Example: python metric_report.py -i data/palmResT2_tfce_tstat_mfwep_m1_mulT.func.gii -s C:\AppsData\OneDrive\data\templateflow\tpl-fsLR\tpl-fsLR_den-32k_hemi-L_midthickness.surf.gii C:\AppsData\OneDrive\data\templateflow\tpl-fsLR\tpl-fsLR_hemi-L_den-32k_desc-vaavg_midthickness.shape.func.gii -a .\data\Desikan.32k.L.label.gii -t 0.5 -less-than -o data\test31
    ''')

def parser():
    parser = argparse.ArgumentParser(description="report surface stats results")
    parser.add_argument('-i', '--input', required=True, help='input a stats file for report')
    parser.add_argument('-t', '--threshold', required=False, default=1, help='value-threshold for wb_command')
    parser.add_argument('--minimum-area', required=False, default=0, help='minimum area for wb_command')
    parser.add_argument('-less-than', action='store_true')
    parser.add_argument('-o', '--output', required=True, help='out prefix')
    parser.add_argument('-s', '--surface', required=True, nargs='+',
                        help='input a surface file [and a surface area file]')
    parser.add_argument('-a', '--atlas', required=True, help='input a atlas file for report brain regions')

    return parser.parse_args()

def compute_surface_area(vertices, faces):
    vertex_areas = np.zeros(vertices.shape[0])
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        vertex_areas[face] += np.linalg.norm(np.cross(v1 - v0, v2 - v0)) / 6.0

    return vertex_areas

def wb_command_find_clusters(args):
    command = [
        'wb_command',
        '-metric-find-clusters',
        args.surface[0],
        args.input,
        args.threshold,
        args.minimum_area,
        str(args.output) + '.threshold.label.func.gii'
    ]

    if args.less_than:
        command.append('-less-than')

    if len(args.surface) > 1:
        command.extend(['-corrected-areas', args.surface[1]])

    command = [str(i) for i in command]

    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout)

    if str(result.stderr) != '':
        print(result.stderr)
        ChildProcessError('wb_command failed')

    command = [
        'wb_command',
        '-metric-math',
        'x * (y >0)',
        str(args.output) + '.threshold.func.gii',
        '-var', 'x', args.input,
        '-var', 'y', str(args.output) + '.threshold.label.func.gii'
    ]
    command = [str(i) for i in command]

    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout)

    if str(result.stderr) != '':
        print(result.stderr)
        ChildProcessError('wb_command failed')


def metric_report(args):
    wb_command_find_clusters(args)
    metric_surface = nib.load(args.surface[0])
    if len(args.surface) == 1:
        vertices_surface, faces_surface = metric_surface.darrays[0].data, metric_surface.darrays[1].data
        metric_area_data = compute_surface_area(vertices_surface, faces_surface)
    else:
        metric_area_data = nib.load(args.surface[1]).darrays[0].data

    metric_infile = nib.load(args.input)
    metric_label = nib.load(str(args.output) + '.threshold.label.func.gii')
    metric_atlas = nib.load(args.atlas)

    metric_surface_data = metric_surface.darrays[0].data
    metric_atlas_data = metric_atlas.darrays[0].data
    metric_atlas_data_map = metric_atlas.labeltable.get_labels_as_dict()

    len_infile_label_equal = True
    if len(metric_infile.darrays) > len(metric_label.darrays):
        len_infile_label_equal = False
        print("将多次使用相同的label文件汇报结果，可能不正确，请检查")
    elif len(metric_infile.darrays) < len(metric_label.darrays):
        ValueError("infile维度小于label维度，请检查")

    for darray_idx in range(len(metric_infile.darrays)):
        cluster_all = []
        cluster_area_info_all = []
        metric_infile_c = metric_infile.darrays[darray_idx].data
        if len_infile_label_equal:
            metric_label_c = metric_label.darrays[darray_idx].data
        else:
            metric_label_c = metric_label.darrays[0].data
        for label_idx in range(np.int64(np.max(metric_label_c))):
            if label_idx + 1 not in np.unique(metric_label_c):
                continue

            if args.less_than:
                peak_vertex_idx = np.array(range(len(metric_label_c)))[metric_label_c == (label_idx + 1)][np.argmin(
                    metric_infile_c[metric_label_c == (label_idx + 1)])]

            else:
                peak_vertex_idx = np.array(range(len(metric_label_c)))[metric_label_c == (label_idx + 1)][np.argmax(
                    metric_infile_c[metric_label_c == (label_idx + 1)])]

            peak_vertex_value = metric_infile_c[peak_vertex_idx]
            peak_vertex_coord = metric_surface_data[peak_vertex_idx]
            peak_region = metric_atlas_data_map[metric_atlas_data[peak_vertex_idx]]
            cluster_area = np.sum(metric_area_data[metric_label_c == (label_idx + 1)])

            cluster_all.append(
                [label_idx+1, peak_vertex_coord[0], peak_vertex_coord[1], peak_vertex_coord[2],
                 peak_vertex_value, cluster_area, peak_region])

            for inter_label_idx in np.unique(metric_atlas_data[metric_label_c == (label_idx + 1)]):
                cluster_area_info_all.append([
                    label_idx + 1, metric_atlas_data_map[inter_label_idx],
                    np.sum(metric_area_data[(metric_label_c == (label_idx + 1)) & (metric_atlas_data == inter_label_idx)]),
                    ])
        cluster_all = pl.DataFrame(
            cluster_all,
            schema=['cluster idx', 'coord-x', 'coord-y', 'coord-z', 'peak value', 'area', 'annot'], orient='row'
        )

        cluster_all.write_csv(args.output + f'_darray-{darray_idx}_cluster_info.csv')
        cluster_area_info_all = pl.DataFrame(
            cluster_area_info_all,
            schema=['cluster idx', 'region', 'area'], orient='row'
        )
        cluster_area_info_all.write_csv(args.output + f'_darray-{darray_idx}_cluster_info_area.csv')


if __name__ == '__main__':
    metric_report(parser())
