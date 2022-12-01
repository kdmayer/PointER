## To Do:

---
Date: 5/8/22
Author: Kevin

- Normalize LiDAR point clouds and save them as .npy format (scaling must be relative to the height of the
 tallest building) :fire:
- Think about folder structure and file names for processing many tiles consecutively :fire:
- Evaluate building footprint polygon data sources (Overpass-Turbo vs. others) :fire:
- Can we combine building point clouds with street view and aerial images? :fire:
---
Date: 24/8/22
Author: Sebastian

- @Kevin: How to download and store LiDAR tiles on server  :+1:
- @Sebastian Normalize LiDAR point clouds and save them as .npy format (scaling must be relative to the height of the
 tallest building) :fire:
- @Sebastian: Finish pipeline for one tile :fire:
- @Sebastian: Contact verisk again for building footprints. :fire:
- @Sebastian: Contact UK open gov. program regarding API for LiDAR :+1:

---
Date: 31/8/22
Author: Sebastian
- @Kevin: Unify conda environment setup across platforms with conda-lock :+1:
- @Kevin: Develop method which adds footprint points to LiDAR-based point cloud :+1:
- @Sebastian: Normalize LiDAR point clouds and save them as .npz format (scaling must be relative to the height of the
 tallest building) --> loop through AOIs, select LiDAR tiles :+1:
- @Sebastian: visualize more buildings and do sanity check of normalization (e.g. tower of bliss tweed mill) :+1:
- @Sebastian: Contact verisk again for building footprints. :+1:

---
Date: 6/9/22
Author: Kevin
- @Sebastian: Inspect quality of Verisk footprints in QGIS :+1:
- @Sebastian: Run through Postgres pipeline setup from scratch and adjust docs accordingly (separate markdown) :+1:
- @Sebastian: Modularize code base for pg-pointcloud script :+1:
- @TBD: Integrate ground points derived from footprint polygons (demo notebook) :fire:
- @Kevin: Execute and test pg-pointcloud script :fire: 
- @Kevin: Re-write pg-pointcloud script in an object-oriented fashion :fire: 

---
Date: 14/9/22
Author: Kevin
- @All: Determine areas of interest for case study in the UK :+1:
- @All: Decide on footprint data source: **Verisk** vs OSM (tendency towards Verisk, check license) :+1:
- @Sebastian: Run pipeline on first set of AOIs and save unnormalized .npz files :+1:
- @Sebastian: Check geocoding service utilized by TUM :+1:
- @TBD: Integrate ground points derived from footprint polygons (demo notebook) :+1:
- @Kevin: Execute and test pg-pointcloud script :+1:
- @Kevin: Re-write pg-pointcloud script in an object-oriented fashion :fire:

---
Date: 30/11/22
Author: Kevin
- @Sebastian: Check why there are so many footprints without associated pointclouds. As an example, Coventry does not generate pointclouds for more than 30% of its footprints :fire:
- @Sebastian: Visualize and analyse pointclouds for quality checks and anomaly detection :fire:
- @Sebastian: Write Nature Data paper and decide on central story thread, i.e., why 3D pointclouds for building energy characteristics :fire:
--> Exemplary key words for literature review: Height, Age, Architecture, Surface-to-Volume ratio, etc.
- @Sebastian: Generate final .geojson for each region including the path to pointcloud file and all the epc features :fire:
--> Can two EPCs end up as the same UPRN?
- @Kevin: Execute singularity container on Sherlock :fire:


Icons:

- Resolved: :+1:
- Unresolved: :fire: