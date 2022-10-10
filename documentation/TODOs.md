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
- @All: Decide on footprint data source: **Verisk** vs OSM (tendency towards Verisk, check license) :fire:
- @Sebastian: Run pipeline on first set of AOIs and save unnormalized .npz files :fire:
- @Sebastian: Check geocoding service utilized by TUM :fire:
- @TBD: Integrate ground points derived from footprint polygons (demo notebook) :fire:
- @Kevin: Execute and test pg-pointcloud script :fire: 
- @Kevin: Re-write pg-pointcloud script in an object-oriented fashion :fire: 

Icons:

- Resolved: :+1:
- Unresolved: :fire: