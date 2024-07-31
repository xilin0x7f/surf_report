# Author: 赩林, xilin0x7f@163.com
import nibabel as nib
import numpy as np
import polars as pl

gii_label = nib.load('data/top3.L.thickness.threshold.label.func.gii')
gii_area = nib.load('data/tpl-fsLR_den-32k_hemi-L_midthickness.area.shape.gii')
gii_surface = nib.load('data/tpl-fsLR_den-32k_hemi-L_midthickness.surf.gii')
gii_infile = nib.load('data/top3.L.thickness.func.gii')
gii_atlas = nib.load('data/Desikan.32k.L.label.gii')

gii_area_data = gii_area.darrays[0].data
gii_surface_data = gii_surface.darrays[0].data
gii_atlas_data = gii_atlas.darrays[0].data
gii_atlas_data_map = gii_atlas.labeltable.get_labels_as_dict()

len_infile_label_equal = True
if len(gii_infile.darrays) > len(gii_label.darrays):
    len_infile_label_equal = False
    print("将多次使用相同的label文件汇报结果，可能不正确，请检查")
elif len(gii_infile.darrays) < len(gii_label.darrays):
    ValueError("infile维度小于label维度，请检查")

for darray_idx in range(len(gii_infile.darrays)):
    cluster_all = []
    cluster_area_info_all = []
    gii_infile_c = gii_infile.darrays[darray_idx].data
    if len_infile_label_equal:
        gii_label_c = gii_label.darrays[darray_idx].data
    else:
        gii_label_c = gii_label.darrays[0].data
    for label_idx in range(np.int64(np.max(gii_label_c))):
        if label_idx + 1 not in np.unique(gii_label_c):
            continue
        peak_vertex_idx = np.array(range(len(gii_label_c)))[gii_label_c == (label_idx + 1)][np.argmax(
            gii_infile_c[gii_label_c == (label_idx + 1)])]

        peak_vertex_value = gii_infile_c[peak_vertex_idx]
        peak_vertex_coord = gii_surface_data[peak_vertex_idx]
        peak_region = gii_atlas_data_map[gii_atlas_data[peak_vertex_idx]]
        cluster_area = np.sum(gii_area_data[gii_label_c == (label_idx + 1)])

        cluster_all.append(
            [label_idx+1, peak_vertex_coord[0], peak_vertex_coord[1], peak_vertex_coord[2],
             peak_vertex_value, cluster_area, peak_region])

        for inter_label_idx in np.unique(gii_atlas_data[gii_label_c == (label_idx + 1)]):
            cluster_area_info_all.append([
                label_idx + 1, gii_atlas_data_map[inter_label_idx],
                np.sum(gii_area_data[(gii_label_c == (label_idx + 1)) & (gii_atlas_data == inter_label_idx)]),
            ])
    cluster_all = pl.DataFrame(
        cluster_all,
        schema=['cluster idx', 'coord-x', 'coord-y', 'coord-z', 'peak value', 'area', 'annot'], orient='row'
    )

    cluster_all.write_csv('cluster_info.csv')
    cluster_area_info_all = pl.DataFrame(
        cluster_area_info_all,
        schema=['cluster idx', 'region', 'area'], orient='row'
    )
    cluster_area_info_all.write_csv('cluster_info_area.csv')

