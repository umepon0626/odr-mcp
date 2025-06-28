from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass, field
import os
import xml.etree.ElementTree as ET
from typing import List, Optional
import logging

# 定数定義
MIN_CURVE_LENGTH = 1.0  # カーブとして認識する最小長さ [m]

@dataclass
class Lane:
    road_id: int
    lane_id: int
    lane_section_id: int

@dataclass
class LinkInfo:
    id: Optional[str] = None

@dataclass
class WidthInfo:
    sOffset: Optional[str] = None
    a: Optional[str] = None
    b: Optional[str] = None
    c: Optional[str] = None
    d: Optional[str] = None

@dataclass
class RoadMarkInfo:
    sOffset: Optional[str] = None
    type: Optional[str] = None
    material: Optional[str] = None
    color: Optional[str] = None
    width: Optional[str] = None
    laneChange: Optional[str] = None

@dataclass
class UserDataInfo:
    travelDir: Optional[str] = None

@dataclass
class GeometryInfo:
    s: Optional[str] = None
    x: Optional[str] = None
    y: Optional[str] = None
    hdg: Optional[str] = None
    length: Optional[str] = None
    curvature: Optional[str] = None

@dataclass
class RoadInfo:
    id: str
    name: Optional[str] = None
    length: Optional[str] = None
    junction: Optional[str] = None
    geometries: List[GeometryInfo] = field(default_factory=list)

@dataclass
class LaneInfo:
    id: str
    type: str
    level: str
    road_id: str
    link: Optional[List[LinkInfo]] = field(default=None)
    width: Optional[List[WidthInfo]] = field(default=None)
    roadMark: Optional[List[RoadMarkInfo]] = field(default=None)
    userData: Optional[List[UserDataInfo]] = field(default=None)

mcp = FastMCP(name="odr-mcp", version="0.1.0")

def extract_geometry_info(geometry_elem) -> GeometryInfo:
    attrib = geometry_elem.attrib
    curvature = None
    if geometry_elem.find('arc') is not None:
        curvature = geometry_elem.find('arc').get('curvature')
    return GeometryInfo(
        s=attrib.get('s'),
        x=attrib.get('x'),
        y=attrib.get('y'),
        hdg=attrib.get('hdg'),
        length=attrib.get('length'),
        curvature=curvature
    )

def parse_roads(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    roads = []
    for road_elem in root.findall('road'):
        road = RoadInfo(
            id=road_elem.get('id', ''),
            name=road_elem.get('name'),
            length=road_elem.get('length'),
            junction=road_elem.get('junction'),
        )
        for geometry_elem in road_elem.findall('./planView/geometry'):
            geometry_info = extract_geometry_info(geometry_elem)
            road.geometries.append(geometry_info)
        roads.append(road)
    return roads

def extract_lane_info(lane_elem, road_id: str) -> LaneInfo:
    attrib = lane_elem.attrib
    def get_child_list(tag, cls):
        return [cls(**c.attrib) for c in lane_elem.findall(tag)] or None
    return LaneInfo(
        id=attrib.get('id', ''),
        type=attrib.get('type', ''),
        level=attrib.get('level', ''),
        road_id=road_id,
        link=get_child_list('link', LinkInfo),
        width=get_child_list('width', WidthInfo),
        roadMark=get_child_list('roadMark', RoadMarkInfo),
        userData=get_child_list('userData', UserDataInfo),
    )

def parse_lanes(file_path):
    lanes = []
    tree = ET.parse(file_path)
    root = tree.getroot()
    for road_elem in root.findall('road'):
        road_id = road_elem.get('id', '')
        for lanes_elem in road_elem.findall('./lanes/laneSection/*/lane'):
            lane_info = extract_lane_info(lanes_elem, road_id)
            lanes.append(lane_info)
    for lane in lanes:
        logging.info(f"Found lane: {lane}")
    return lanes

@mcp.tool()
def find_lane_with_r(r: float, file_path: str) -> Optional[LaneInfo]:
    """find the lane with the r [m] from odr data.

    Args:
        r (float): the r [m] (曲率半径)
        file_path (str): 探索対象のOpenDRIVEファイルの絶対パス

    Returns:
        LaneInfo: the lane with the r [m] (曲率がrに最も近いroadのlane)
    """
    # 道路の曲率情報を取得
    roads = parse_roads(file_path)
    lanes = parse_lanes(file_path)
    
    closest_road_id = None
    min_diff = float('inf')
    closest_curvature = None
    
    # 曲率がrに最も近いroadを探す
    for road in roads:
        for geometry in road.geometries:
            # curvatureが存在し、かつlengthがMIN_CURVE_LENGTH以上の場合のみ探索
            if geometry.curvature is not None and geometry.length is not None:
                try:
                    length_val = float(geometry.length)
                    curvature_val = float(geometry.curvature)
                    
                    # lengthがMIN_CURVE_LENGTH以上の場合のみ処理
                    if length_val >= MIN_CURVE_LENGTH:
                        # 曲率から曲率半径を計算 (R = 1/curvature)
                        radius = 1.0 / curvature_val if curvature_val != 0 else float('inf')
                        diff = abs(radius - r)
                        if diff < min_diff:
                            min_diff = diff
                            closest_road_id = road.id
                            closest_curvature = curvature_val
                except (ValueError, ZeroDivisionError):
                    continue
    
    # 最も近いcurvatureをログ出力
    if closest_curvature is not None:
        logging.info(f"最も近い曲率: {closest_curvature}")
        logging.info(f"対応する曲率半径: {1.0 / closest_curvature}")
        logging.info(f"探索した曲率半径: {r}")
        logging.info(f"差: {min_diff}")
    
    # 該当するroadのlaneを返す
    if closest_road_id is not None:
        for lane in lanes:
            if lane.road_id == closest_road_id and lane.type != "none":
                return lane
    
    return None

@mcp.tool()
def find_road_with_r(r: float, file_path: str) -> Optional[RoadInfo]:
    """find the road with the r [m] from odr data.

    Args:
        r (float): the r [m] (曲率半径)
        file_path (str): 探索対象のOpenDRIVEファイルの絶対パス

    Returns:
        RoadInfo: the road with the r [m] (曲率がrに最も近いroad)
    """
    roads = parse_roads(file_path)
    closest_road = None
    min_diff = float('inf')
    closest_curvature = None

    for road in roads:
        for geometry in road.geometries:
            if geometry.curvature is not None and geometry.length is not None:
                try:
                    length_val = float(geometry.length)
                    curvature_val = float(geometry.curvature)
                    if length_val >= MIN_CURVE_LENGTH:
                        radius = 1.0 / curvature_val if curvature_val != 0 else float('inf')
                        diff = abs(radius - r)
                        if diff < min_diff:
                            min_diff = diff
                            closest_road = road
                            closest_curvature = curvature_val
                except (ValueError, ZeroDivisionError):
                    continue

    if closest_curvature is not None:
        logging.info(f"最も近い曲率: {closest_curvature}")
        logging.info(f"対応する曲率半径: {1.0 / closest_curvature}")
        logging.info(f"探索した曲率半径: {r}")
        logging.info(f"差: {min_diff}")

    return closest_road

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # MCPサーバーとして実行
    mcp.run()