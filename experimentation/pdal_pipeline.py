from typing import List
from tqdm import tqdm

import pdal
import json
import random


def run_pdal_pipeline(footprint_list: List = None, las_file_path: str = None, random_sample_size: int = None):
    if random_sample_size == None:
        footprint_list = footprint_list
    else:
        # Sample a subset of the footprint polygons for debugging purposes
        footprint_list = random.sample(footprint_list, random_sample_size)

    for i in tqdm(range(len(footprint_list))):
        pipeline_definition = {

            'pipeline': [
                las_file_path,
                {
                    "type": "filters.crop",
                    "polygon": footprint_list[i]
                },
                {
                    "type": "writers.las",
                    "filename": f"cropped_{i}.las"
                }
            ]
        }

        pipeline = pdal.Pipeline(json.dumps(pipeline_definition))
        pipeline.execute()
    return



