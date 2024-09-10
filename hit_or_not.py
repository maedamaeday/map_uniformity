import numpy as np
import json
import time
from turfpy.measurement import boolean_point_in_polygon
from geojson import Point, MultiPolygon, Feature

import my_read_kml as my_rk

from typing import Optional
import argparse

def_n_try = 100

def main(
        given_pref_id: int,
        input_json: str = "prefectures.geojson",
        n_try: int = def_n_try, 
        rand_seed: Optional[int] = None,
):

    start = time.time()
    rng = np.random.default_rng(seed=rand_seed)
    thres = [(i+1)*0.01 for i in range(50)]
    n_close = [0 for _ in thres]
    i_closest_non_hit = [[] for _ in thres]
    
    points = my_rk.main()
    
    with open(input_json) as f:
        prefectures = json.load(f)

    pref_features = {}
    for features in prefectures["features"]:
        pref_id = features["properties"]["pref"]
        pref_name = features["properties"]["name"]
        coordinates = features["geometry"]["coordinates"]
        n_regions = len(coordinates)
        polygons = Feature(geometry=MultiPolygon(coordinates))
        pref_features[pref_id] = {
            "name": pref_name,
            "n_regions": n_regions,
            "polygons": polygons,
        }
        if pref_id!=given_pref_id:
            continue
        print(f"{pref_id}, {pref_name} : {n_regions}")
        x_mins, x_maxs, y_mins, y_maxs, areas = [], [], [], [], []
        for region in features["geometry"]["coordinates"]:
            x, y = [], []
            for x_, y_ in region[0]:
                x.append(x_)
                y.append(y_)
            x_min, x_max = min(x), max(x)
            y_min, y_max = min(y), max(y)
            x_mins.append(x_min)
            x_maxs.append(x_max)
            y_mins.append(y_min)
            y_maxs.append(y_max)
            areas.append((x_max-x_min)*(y_max-y_min))
        total_area = sum(areas)
            
        Xs, Ys = [], []
        for name, xy in points.items():
            x, y = xy
            point = Feature(geometry=Point([x, y]))
            if boolean_point_in_polygon(point, polygons):
                print(len(Xs), name, x, y)
                Xs.append(x)
                Ys.append(y)
        Xs = np.array(Xs)
        Ys = np.array(Ys)
        print("----------")
        
        n_shot = 0
        n_hit = 0
        d = []
        while n_hit<n_try:
            while True:
                n_shot += 1
                r, x_, y_ = rng.random(3)
                ith_region = 0
                area_sum = areas[ith_region]/total_area
                while r>area_sum:
                    ith_region += 1
                    area_sum += areas[ith_region]/total_area
                x = x_mins[ith_region]+x_*(x_maxs[ith_region]-x_mins[ith_region])
                y = y_mins[ith_region]+y_*(y_maxs[ith_region]-y_mins[ith_region])
                point = Feature(geometry=Point([x, y]))
                # probably not correct when
                #  - region rectangles have overlap
                if boolean_point_in_polygon(point, polygons):
                    break
            n_hit += 1

            dists = np.hypot(Xs-x, Ys-y)
            min_dist = np.min(dists)
            i_min = np.argmin(dists)
            d.append(min_dist)
            for i_thre, thre in enumerate(thres):
                if min_dist<thre:
                    n_close[i_thre] += 1
                else:
                    i_closest_non_hit[i_thre].append(i_min)

        print(f"n_hit={n_hit} / n_shot={n_shot}")
        print(f"min={np.min(d)}, max={np.max(d)} "
              f"/ mean={np.mean(d)} +/- {np.std(d)}")
        break

    for thre, n, i_closest in zip(thres, n_close, i_closest_non_hit):
        if len(i_closest)>0:
            ith_places, counts = np.unique(
                i_closest,
                return_counts=True,
            )
            mode_place = ith_places[np.argmax(counts)]
            mode_n = np.max(counts)
        else:
            mode_place = None
            mode_n = None
        print(thre, n/n_hit, mode_place, mode_n)
    
    print(f"{time.time()-start} s")
        
    return

if __name__=="__main__":

    parser = argparse.ArgumentParser(
        description="find points from kmz in given prefecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "given_pref_id",
        type=int,
        help="pref_id",
    )
    parser.add_argument(
        "-n", "--n_try",
        type=int,
        default=def_n_try,
        help="# of random points to be generated",
    )
    parser.add_argument(
        "-r", "--rand_seed",
        type=int,
        default=None,
        help="random number seed",
    )

    args = parser.parse_args()
    main(
        given_pref_id=args.given_pref_id,
        n_try=args.n_try, 
        rand_seed=args.rand_seed,
    )
