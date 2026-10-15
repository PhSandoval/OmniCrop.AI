"""
Motor Geoespacial e Utilitários PostGIS para OmniCrop AI.
Cálculo de limites territoriais, polígonos de talhões, áreas geodésicas e renderização de mapas Folium.
"""
import math
import json
import folium
from folium.plugins import LocateControl


def generate_parcel_polygon(
    lat: float,
    lon: float,
    area_ha: float,
    aspect_ratio: float = 1.3,
    orientation_deg: float = 15.0,
) -> dict:
    """
    Gera um polígono GeoJSON representando os limites do talhão com base no centroide e área (hectares).
    Utiliza projeção WGS84 em metros ajustada pela latitude local.
    """
    area_m2 = max(float(area_ha), 1.0) * 10000.0
    w_m = math.sqrt(area_m2 / aspect_ratio)
    h_m = w_m * aspect_ratio

    dx_m = w_m / 2.0
    dy_m = h_m / 2.0

    rad = math.radians(orientation_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    # 4 vértices em metros relativos ao centro
    corners_m = [
        (-dx_m * cos_a - -dy_m * sin_a, -dx_m * sin_a + -dy_m * cos_a),
        (dx_m * cos_a - -dy_m * sin_a, dx_m * sin_a + -dy_m * cos_a),
        (dx_m * cos_a - dy_m * sin_a, dx_m * sin_a + dy_m * cos_a),
        (-dx_m * cos_a - dy_m * sin_a, -dx_m * sin_a + dy_m * cos_a),
    ]

    lat_rad = math.radians(lat)
    m_per_deg_lat = 111320.0
    m_per_deg_lon = 111320.0 * math.cos(lat_rad)

    coords = []
    for x_m, y_m in corners_m:
        p_lat = round(lat + (y_m / m_per_deg_lat), 6)
        p_lon = round(lon + (x_m / m_per_deg_lon), 6)
        coords.append([p_lon, p_lat])

    # Fecha o anel linear do polígono
    coords.append(coords[0])

    return {"type": "Polygon", "coordinates": [coords]}


def calculate_geodesic_area_ha(coordinates: list) -> float:
    """
    Calcula a área geodésica real em hectares de um anel de coordenadas [[lon, lat], ...].
    Aplica Shoelace esférico calibrado por grau métrico.
    """
    if not coordinates or len(coordinates) < 4:
        return 0.0

    n = len(coordinates)
    lat_mean = sum(c[1] for c in coordinates) / n
    lat_rad = math.radians(lat_mean)
    m_per_deg_lat = 111320.0
    m_per_deg_lon = 111320.0 * math.cos(lat_rad)

    area = 0.0
    for i in range(n - 1):
        x1 = coordinates[i][0] * m_per_deg_lon
        y1 = coordinates[i][1] * m_per_deg_lat
        x2 = coordinates[i + 1][0] * m_per_deg_lon
        y2 = coordinates[i + 1][1] * m_per_deg_lat
        area += x1 * y2 - x2 * y1

    area_m2 = abs(area) / 2.0
    return round(area_m2 / 10000.0, 2)


def calculate_perimeter_km(coordinates: list) -> float:
    """
    Calcula o perímetro total do polígono em quilômetros via fórmula de Haversine.
    """
    if not coordinates or len(coordinates) < 4:
        return 0.0

    R = 6371.0  # Raio da Terra em km
    perim_km = 0.0

    for i in range(len(coordinates) - 1):
        lon1, lat1 = coordinates[i]
        lon2, lat2 = coordinates[i + 1]

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)

        a = (
            math.sin(dphi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        perim_km += R * c

    return round(perim_km, 3)


def polygon_to_postgis_wkt(geojson_dict: dict) -> str:
    """
    Converte um dicionário GeoJSON Polygon em string WKT (Well-Known Text) para PostGIS ST_GeomFromText.
    """
    if not geojson_dict or "coordinates" not in geojson_dict:
        return ""
    rings = geojson_dict["coordinates"]
    ring_strs = []
    for ring in rings:
        pt_strs = [f"{lon} {lat}" for lon, lat in ring]
        ring_strs.append("(" + ", ".join(pt_strs) + ")")
    return f"POLYGON({', '.join(ring_strs)})"


def postgis_wkt_to_geojson(wkt_str: str) -> dict:
    """
    Converte string WKT de PostGIS em GeoJSON Polygon.
    """
    if not wkt_str or "POLYGON" not in wkt_str.upper():
        return {}
    clean = wkt_str.replace("POLYGON", "").replace("polygon", "").strip()
    clean = clean.lstrip("(").rstrip(")")
    raw_rings = clean.split("), (")
    rings = []
    for raw_ring in raw_rings:
        pts = raw_ring.replace("(", "").replace(")", "").split(",")
        ring = []
        for pt in pts:
            parts = pt.strip().split()
            if len(parts) >= 2:
                ring.append([float(parts[0]), float(parts[1])])
        if ring:
            rings.append(ring)
    return {"type": "Polygon", "coordinates": rings}


def ensure_farm_boundary(farm: dict) -> dict:
    """
    Garante que a fazenda possui os limites territoriais (boundary_geojson).
    Se não possuir ou for nulo no banco, gera automaticamente a geometria PostGIS.
    """
    farm_copy = dict(farm)
    bg = farm_copy.get("boundary_geojson")

    if isinstance(bg, str):
        try:
            bg = json.loads(bg)
        except Exception:
            bg = None

    if not bg or not isinstance(bg, dict) or "coordinates" not in bg:
        lat = float(farm_copy.get("lat", -21.1704))
        lon = float(farm_copy.get("lon", -47.8103))
        area = float(farm_copy.get("area_ha", 100.0))
        bg = generate_parcel_polygon(lat, lon, area)

    farm_copy["boundary_geojson"] = bg
    return farm_copy


def get_polygon_bounds_and_center(coordinates: list) -> tuple:
    """
    Retorna ([centro_lat, centro_lon], [[sul, oeste], [norte, leste]]) para ajuste de câmera no mapa.
    """
    lons = [c[0] for c in coordinates]
    lats = [c[1] for c in coordinates]

    center = [sum(lats) / len(lats), sum(lons) / len(lons)]
    bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
    return center, bounds


def create_farm_folium_map(
    farms: list[dict],
    selected_farm_id: str = None,
    height: int = 480,
) -> folium.Map:
    """
    Constrói mapa Folium interativo de alta performance com camadas Esri Satélite,
    OpenStreetMap e renderização otimizada dos polígonos territoriais PostGIS.
    """
    # Encontra fazenda ativa
    target_farm = None
    if selected_farm_id:
        target_farm = next((f for f in farms if str(f.get("id")) == str(selected_farm_id)), None)

    if not target_farm and farms:
        target_farm = farms[0]

    lat = float(target_farm.get("lat", -21.1704)) if target_farm else -21.1704
    lon = float(target_farm.get("lon", -47.8103)) if target_farm else -47.8103

    m = folium.Map(location=[lat, lon], zoom_start=14, tiles=None)

    # 1. Camada de Satélite de Alta Resolução (Esri World Imagery)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satélite (Esri)",
        overlay=False,
        control=True,
    ).add_to(m)

    # 2. Camada Híbrida / Ruas (OpenStreetMap)
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="Ruas e Limites (OSM)",
        overlay=False,
        control=True,
    ).add_to(m)

    # 3. Adiciona Botão de GPS Localização
    LocateControl(auto_start=False, position="bottomright").add_to(m)

    # 4. Renderiza Polígonos Territoriais de todas as fazendas do usuário
    selected_bounds = None

    for f in farms:
        f_safe = ensure_farm_boundary(f)
        is_selected = str(f.get("id")) == str(selected_farm_id) if selected_farm_id else False

        bg = f_safe.get("boundary_geojson", {})
        coords = bg.get("coordinates", [[]])[0]

        if not coords:
            continue

        border_color = "#00E676" if is_selected else "#4FC3F7"
        fill_color = "#00E676" if is_selected else "#0288D1"
        fill_opacity = 0.35 if is_selected else 0.15
        weight = 3 if is_selected else 1.5

        geo_area = calculate_geodesic_area_ha(coords)
        perim = calculate_perimeter_km(coords)

        popup_html = f"""
        <div style="font-family:sans-serif; min-width:180px; padding:4px;">
            <b style="color:#2E7D32; font-size:14px;">🌾 {f.get('farm_name', 'Talhão')}</b><br>
            <span style="font-size:11px; color:#555;">{f.get('city', '')} · {f.get('tipo_cultura', 'Cana-de-Açúcar')}</span>
            <hr style="margin:6px 0;">
            <span style="font-size:12px;"><b>Área:</b> {geo_area:.1f} ha (Cadastrada: {f.get('area_ha', 0)} ha)</span><br>
            <span style="font-size:12px;"><b>Perímetro:</b> {perim:.2f} km</span><br>
            <span style="font-size:12px;"><b>Variedade:</b> {f.get('variedade', 'Padrão')}</span><br>
            <span style="font-size:11px; color:#777;">Lat {f.get('lat', 0):.4f}, Lon {f.get('lon', 0):.4f}</span>
        </div>
        """

        folium.GeoJson(
            bg,
            style_function=lambda x, bc=border_color, fc=fill_color, fo=fill_opacity, w=weight: {
                "fillColor": fc,
                "color": bc,
                "weight": w,
                "fillOpacity": fo,
            },
            tooltip=f"🌾 {f.get('farm_name', 'Talhão')} ({geo_area:.1f} ha)",
            popup=folium.Popup(popup_html, max_width=300),
        ).add_to(m)

        # Marcador central
        f_lat = float(f.get("lat", 0))
        f_lon = float(f.get("lon", 0))
        pin_color = "green" if is_selected else "blue"
        folium.Marker(
            [f_lat, f_lon],
            tooltip=f"{f.get('farm_name', '')} (Centroide)",
            icon=folium.Icon(color=pin_color, icon="leaf", prefix="fa"),
        ).add_to(m)

        if is_selected:
            _, selected_bounds = get_polygon_bounds_and_center(coords)

    if selected_bounds:
        m.fit_bounds(selected_bounds)

    folium.LayerControl(position="topright").add_to(m)
    return m
