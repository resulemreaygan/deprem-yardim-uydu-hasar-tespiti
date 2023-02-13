"""
Author: Resul Emre AYGAN
"""

from osgeo import ogr
from osgeo.ogr import GetDriverByName
from osgeo.osr import OAMS_TRADITIONAL_GIS_ORDER, SpatialReference, CoordinateTransformation
from osgeo.gdal import __version__ as osgeo_version
from shapely.geometry import Polygon, MultiPolygon
from shapely import wkt


shape_driver = GetDriverByName("ESRI Shapefile")


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
            polygon = ogr.CreateGeometryFromWkt(polygon.wkt)

        if not isinstance(polygon, ogr.Geometry):
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


def clip_shapefile_with_shapefile(input_shapefile, clip_shapefile, output_shapefile):
    try:
        in_ds = shape_driver.Open(input_shapefile, 0)
        in_layer = in_ds.GetLayer()

        # print(in_layer.GetFeatureCount())

        in_clip_ds = shape_driver.Open(clip_shapefile, 0)
        in_clip_layer = in_clip_ds.GetLayer()
        # print(in_clip_layer.GetFeatureCount())

        out_ds = shape_driver.CreateDataSource(output_shapefile)
        out_layer = out_ds.CreateLayer('final', geom_type=ogr.wkbMultiPolygon)

        ogr.Layer.Clip(in_layer, in_clip_layer, out_layer)
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

        layer = data_source.CreateLayer("polygons", srs, ogr.wkbPolygon)

        feature = ogr.Feature(layer.GetLayerDefn())

        polygon = ogr.CreateGeometryFromWkt(geom_wkt)

        feature.SetGeometry(polygon)

        layer.CreateFeature(feature)
        feature = None
        data_source = None

        return True
    except Exception as error:
        print(f"Shapefile olusturulurken hata olustu: {error} - {output_path}")
        return False
