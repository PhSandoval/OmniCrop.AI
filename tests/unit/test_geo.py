import pytest
import sys
from pathlib import Path
import folium

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.utils.geo import (
    generate_parcel_polygon,
    calculate_geodesic_area_ha,
    calculate_perimeter_km,
    polygon_to_postgis_wkt,
    postgis_wkt_to_geojson,
    ensure_farm_boundary,
    create_farm_folium_map,
    get_polygon_bounds_and_center,
)


def test_generate_parcel_polygon_structure():
    """Valida a conformidade da estrutura do polígono GeoJSON (WGS84) gerado para o talhão."""
    poly = generate_parcel_polygon(-21.1704, -47.8103, 100.0)

    assert poly["type"] == "Polygon"
    assert "coordinates" in poly
    coords = poly["coordinates"][0]

    # Um polígono linear válido deve ter pelo menos 4 pontos e estar fechado (primeiro == último)
    assert len(coords) == 5
    assert coords[0] == coords[-1]

    # Todos os pontos devem estar em torno das coordenadas informadas
    for lon, lat in coords:
        assert abs(lat - (-21.1704)) < 0.1
        assert abs(lon - (-47.8103)) < 0.1


def test_calculate_geodesic_area_accuracy():
    """Valida a precisão da fórmula de Shoelace geodésica em hectares."""
    # Gera um talhão de 150 hectares
    poly_150 = generate_parcel_polygon(-21.1704, -47.8103, 150.0)
    coords = poly_150["coordinates"][0]
    calc_area = calculate_geodesic_area_ha(coords)

    # Margem de tolerância aceitável menor que 1.5%
    assert abs(calc_area - 150.0) < 2.0

    # Teste de caso de borda: dados vazios
    assert calculate_geodesic_area_ha([]) == 0.0
    assert calculate_geodesic_area_ha([[0, 0], [1, 1]]) == 0.0


def test_calculate_perimeter_km():
    """Valida o cálculo do perímetro geodésico (Haversine) do talhão."""
    # Um quadrado de 100 ha (1 km x 1 km) tem perímetro teórico aproximado de ~4 km
    poly_100 = generate_parcel_polygon(-21.1704, -47.8103, 100.0, aspect_ratio=1.0)
    coords = poly_100["coordinates"][0]
    perim = calculate_perimeter_km(coords)

    assert 3.8 < perim < 4.2
    assert calculate_perimeter_km([]) == 0.0


def test_polygon_to_postgis_wkt_conversion():
    """Valida a conversão bidirecional entre GeoJSON e PostGIS WKT (Well-Known Text)."""
    poly = generate_parcel_polygon(-21.1704, -47.8103, 50.0)
    wkt = polygon_to_postgis_wkt(poly)

    assert wkt.startswith("POLYGON((")
    assert wkt.endswith("))")
    assert "-47." in wkt
    assert "-21." in wkt

    # Reconversão para GeoJSON
    reconstructed = postgis_wkt_to_geojson(wkt)
    assert reconstructed["type"] == "Polygon"
    assert len(reconstructed["coordinates"][0]) == len(poly["coordinates"][0])


def test_ensure_farm_boundary_auto_generation():
    """Valida o preenchimento automático de boundary_geojson se a fazenda não possuir polígono gravado."""
    farm_without_geo = {
        "id": "farm_001",
        "farm_name": "Talhão Sem Geo",
        "lat": -21.17,
        "lon": -47.81,
        "area_ha": 80.0,
    }

    farm_safe = ensure_farm_boundary(farm_without_geo)
    assert "boundary_geojson" in farm_safe
    assert farm_safe["boundary_geojson"]["type"] == "Polygon"
    assert len(farm_safe["boundary_geojson"]["coordinates"][0]) == 5

    # Não deve sobrescrever se já tiver polígono válido
    existing_poly = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
    farm_with_geo = {"id": "farm_002", "boundary_geojson": existing_poly}
    farm_preserved = ensure_farm_boundary(farm_with_geo)
    assert farm_preserved["boundary_geojson"] == existing_poly


def test_create_farm_folium_map_rendering():
    """Garante que a construção do mapa interativo Folium ocorre sem erros de renderização."""
    farms = [
        {"id": "f1", "farm_name": "Talhão A", "lat": -21.17, "lon": -47.81, "area_ha": 100},
        {"id": "f2", "farm_name": "Talhão B", "lat": -21.19, "lon": -47.83, "area_ha": 50},
    ]

    m = create_farm_folium_map(farms, selected_farm_id="f1")
    assert isinstance(m, folium.Map)
    
    # Verifica se os layers foram adicionados ao mapa
    layer_names = [layer.layer_name for layer in m._children.values() if hasattr(layer, "layer_name")]
    assert "Satélite (Esri)" in layer_names
    assert "Ruas e Limites (OSM)" in layer_names

    # Teste de mapa sem selected_farm_id (cobre fallback target_farm = farms[0])
    m_no_sel = create_farm_folium_map(farms, selected_farm_id=None)
    assert isinstance(m_no_sel, folium.Map)

    # Teste de fazenda com coordenadas vazias (cobre continue em coords)
    empty_coord_farm = [{"id": "f_empty", "lat": -21.0, "lon": -47.0, "boundary_geojson": {"type": "Polygon", "coordinates": [[]]}}]
    m_empty_coords = create_farm_folium_map(empty_coord_farm)
    assert isinstance(m_empty_coords, folium.Map)

    # Teste de lista de fazendas vazia
    m_none = create_farm_folium_map([])
    assert isinstance(m_none, folium.Map)


def test_geo_edge_cases_and_wkt_parsing():
    """Cobre casos de borda de parsing WKT e serialização de boundary_geojson em string."""
    # 1. polygon_to_postgis_wkt vazio
    assert polygon_to_postgis_wkt({}) == ""
    assert polygon_to_postgis_wkt(None) == ""
    assert polygon_to_postgis_wkt({"type": "Polygon"}) == ""

    # 2. postgis_wkt_to_geojson vazio ou não-polígono
    assert postgis_wkt_to_geojson("") == {}
    assert postgis_wkt_to_geojson(None) == {}
    assert postgis_wkt_to_geojson("POINT(10 20)") == {}

    # 3. ensure_farm_boundary com string JSON válida
    valid_str_json = '{"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}'
    res_str = ensure_farm_boundary({"id": "f_str", "boundary_geojson": valid_str_json})
    assert isinstance(res_str["boundary_geojson"], dict)
    assert res_str["boundary_geojson"]["type"] == "Polygon"

    # 4. ensure_farm_boundary com string JSON inválida (cobre bloco except)
    invalid_str = '{not a valid json}'
    res_inv = ensure_farm_boundary({"id": "f_inv", "boundary_geojson": invalid_str, "lat": -21.0, "lon": -47.0})
    assert isinstance(res_inv["boundary_geojson"], dict)
    assert len(res_inv["boundary_geojson"]["coordinates"][0]) == 5
