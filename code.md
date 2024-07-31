
find cluster 
```zsh
### extract cluster id
wb_command -metric-find-clusters tpl-fsLR_den-32k_hemi-L_midthickness.surf.gii top3.L.thickness.func.gii 4.85 0 top3.L.thickness.threshold.label.func.gii
wb_command -metric-find-clusters tpl-fsLR_den-32k_hemi-R_midthickness.surf.gii top3.R.thickness.func.gii 4.85 0 top3.R.thickness.threshold.lable.func.gii

### extract cluster for visual
wb_command -metric-math 'x * (y > 0)' top3.L.thickness.threshold.func.gii -var x top3.L.thickness.func.gii -var y top3.L.thickness.threshold.label.func.gii
wb_command -metric-math 'x * (y > 0)' top3.R.thickness.threshold.func.gii -var x top3.R.thickness.func.gii -var y top3.R.thickness.threshold.label.func.gii
```

编译成单个文件

```zsh
pyinstaller --onefile metric_report.py
```