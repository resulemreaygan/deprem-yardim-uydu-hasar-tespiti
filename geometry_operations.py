"""
Author: Resul Emre AYGAN
"""

import geopandas as gpd
from osgeo.gdal import __version__ as osgeo_version
from osgeo.ogr import GetDriverByName, wkbPolygon, Feature, CreateGeometryFromWkt, wkbMultiPolygon, Layer, Geometry
from osgeo.osr import OAMS_TRADITIONAL_GIS_ORDER, SpatialReference, CoordinateTransformation
from shapely import wkt
from shapely.geometry import Polygon, MultiPolygon

shape_driver = GetDriverByName("ESRI Shapefile")

if shape_driver is None:
    raise ValueError("Can't find ESRI Shapefile Driver")


def lon_lat_to_geom(lon, lat):
    geom_str = "POLYGON (("
    for index in range(len(lon)):
        geom_str += str(lon[index]) + " " + str(lat[index]) + ","
    geom_str += str(lon[0]) + " " + str(lat[0]) + " ))"

    return wkt.loads(geom_str)


def check_epsg(projection):
    utm_sr = SpatialReference(wkt=projection)
    epsg = int(utm_sr.GetAttrValue('AUTHORITY', 1))

    return epsg


def bounds_to_polygon(geom_bounds):
    return Polygon([(geom_bounds[0], geom_bounds[1]), (geom_bounds[0], geom_bounds[3]),
                    (geom_bounds[2], geom_bounds[3]), (geom_bounds[2], geom_bounds[1])])


def transform_polygon_osr(polygon, src_epsg=4326, dst_epsg=3857):
    try:
        if isinstance(polygon, Polygon) or isinstance(polygon, MultiPolygon):
            polygon = CreateGeometryFromWkt(polygon.wkt)

        if not isinstance(polygon, Geometry):
            print("Geometri ogr geometri formatinda degil!")
            return False

        src = SpatialReference()
        tgt = SpatialReference()

        src.ImportFromEPSG(src_epsg)
        tgt.ImportFromEPSG(dst_epsg)

        if int(osgeo_version[0]) >= 3:
            # GDAL 3 changes axis order: https://github.com/OSGeo/gdal/issues/1546
            src.SetAxisMappingStrategy(OAMS_TRADITIONAL_GIS_ORDER)
            tgt.SetAxisMappingStrategy(OAMS_TRADITIONAL_GIS_ORDER)

        transformer = CoordinateTransformation(src, tgt)

        polygon.Transform(transformer)

        return wkt.loads(polygon.ExportToWkt())

    except Exception as error:
        print(f"Poligon transform isleminde hata olustu: {error}")


def clip_shapefile_with_shapefile(input_shapefile, clip_shapefile, output_shapefile, epsg=4326):
    try:
        srs = SpatialReference()
        srs.ImportFromEPSG(epsg)

        in_ds = shape_driver.Open(input_shapefile, 0)

        if in_ds is None:
            raise IOError(f'Shapefile acilamadi! {input_shapefile}')

        in_layer = in_ds.GetLayer()

        # print(in_layer.GetFeatureCount())

        in_clip_ds = shape_driver.Open(clip_shapefile, 0)

        if in_clip_ds is None:
            raise IOError(f'Shapefile acilamadi! {clip_shapefile}')

        in_clip_layer = in_clip_ds.GetLayer()
        # print(in_clip_layer.GetFeatureCount())

        out_ds = shape_driver.CreateDataSource(output_shapefile)
        out_layer = out_ds.CreateLayer('final', srs, wkbMultiPolygon)

        Layer.Clip(in_layer, in_clip_layer, out_layer)
        # print(out_layer.GetFeatureCount())

        in_ds = None
        # in_clip_ds = None
        out_ds = None

        return True
    except Exception as error:
        print(f"Shapefile kesme isleminde sorun olustu. Hata: {error}")
        return False


def create_shapefile(geom_wkt, output_path, epsg=3857):
    try:
        data_source = shape_driver.CreateDataSource(output_path)

        srs = SpatialReference()
        srs.ImportFromEPSG(epsg)

        layer = data_source.CreateLayer("polygons", srs, wkbPolygon)

        feature = Feature(layer.GetLayerDefn())

        polygon = CreateGeometryFromWkt(geom_wkt)

        feature.SetGeometry(polygon)

        layer.CreateFeature(feature)
        feature = None
        data_source = None

        return True
    except Exception as error:
        print(f"Shapefile olusturulurken hata olustu: {error} - {output_path}")
        return False


def read_shapefile_with_gpd(shapefile_path):
    return gpd.read_file(shapefile_path)


def get_categories_from_shapefile(shapefile_path):
    vector_data = read_shapefile_with_gpd(shapefile_path=shapefile_path)

    if 'damage_gra' in vector_data.keys():
        return list(vector_data['damage_gra'].unique())
    else:
        return []


def save_gdf_to_shapefile(output_path, epsg, gdf_data):
    try:
        if not gdf_data.empty:
            gdf_data.to_file(output_path, driver='ESRI Shapefile', crs='EPSG:' + str(epsg))
            return True
        else:
            return False
    except Exception as error:
        print(f"Geodataframe olusturulamadi! {error} - {output_path}")
        return False
