# Author: 赩林, xilin0x7f@163.com
import templateflow
import templateflow.api as tflow

templates = tflow.templates()

for template in templates:
    if template == "MNI152NLin6Asym":
        continue

    tflow.get(template)

# tflow.get("MNI152NLin6Asym")