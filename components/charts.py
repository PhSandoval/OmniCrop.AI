"""Reusable Plotly chart builders."""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def _layout(fig: go.Figure, height: int = 200) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="rgba(180,230,180,.80)",
        xaxis=dict(showgrid=False, linecolor="rgba(100,200,100,.15)",
                   tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor="rgba(100,200,100,.10)",
                   linecolor="rgba(100,200,100,.15)", tickfont=dict(size=9)),
        showlegend=False,
    )
    return fig


def ndvi_gauge(value: float, title: str = "NDVI") -> go.Figure:
    if value >= 0.6:
        color = "#69F0AE"
    elif value >= 0.4:
        color = "#FFD600"
    else:
        color = "#EF5350"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"font": {"size": 38, "color": color, "family": "Inter"}},
        title={"text": title, "font": {"size": 12, "color": "rgba(180,230,180,.70)", "family": "Inter"}},
        gauge={
            "axis": {"range": [0, 1],
                     "tickcolor": "rgba(180,230,180,.40)",
                     "tickfont": {"color": "rgba(180,230,180,.50)", "size": 9}},
            "bar": {"color": color, "thickness": 0.22},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 0.4],  "color": "rgba(239,83,80,.12)"},
                {"range": [0.4, 0.6], "color": "rgba(255,214,0,.12)"},
                {"range": [0.6, 1.0], "color": "rgba(105,240,174,.12)"},
            ],
            "threshold": {"line": {"color": color, "width": 3},
                          "thickness": 0.80, "value": value},
        },
    ))
    fig.update_layout(
        height=220, margin=dict(t=40, b=10, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)", font_color="#E8F5E9",
    )
    return fig


def ndvi_line(hist: pd.DataFrame) -> go.Figure:
    fig = px.line(hist, x="date", y="ndvi_medio",
                  color_discrete_sequence=["#69F0AE"])
    fig.update_traces(line_width=2)
    fig.add_hrect(y0=0.6, y1=1.0, fillcolor="rgba(105,240,174,.05)", line_width=0)
    fig.add_hrect(y0=0, y1=0.4, fillcolor="rgba(239,83,80,.05)", line_width=0)
    return _layout(fig)


def rain_bars(hist: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=hist["date"], y=hist["precipitacao_total"],
                marker_color="rgba(100,181,246,.75)", marker_line_width=0)
    return _layout(fig)


def temp_lines(hist: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist["date"], y=hist["t_max"], name="Max",
                             line=dict(color="#EF5350", width=1.8)))
    fig.add_trace(go.Scatter(x=hist["date"], y=hist["t_min"], name="Min",
                             line=dict(color="#64B5F6", width=1.8)))
    _layout(fig)
    fig.update_layout(showlegend=True,
                      legend=dict(font=dict(size=9, color="rgba(180,230,180,.70)"),
                                  bgcolor="rgba(0,0,0,0)", x=0, y=1))
    return fig


def ndvi_full_history(df: pd.DataFrame) -> go.Figure:
    fig = px.line(df, x="date", y="ndvi_medio", color_discrete_sequence=["#69F0AE"])
    fig.update_traces(line_width=1.5)
    return _layout(fig, height=280)


def seasonal_box(df: pd.DataFrame) -> go.Figure:
    df = df.copy()
    df["mes"] = df["date"].dt.month
    
    meses_pt = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 
                7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}
    
    monthly_rain = df.groupby("mes")["precipitacao_total"].sum().reset_index()
    monthly_rain["mes_nome"] = monthly_rain["mes"].map(meses_pt)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly_rain["mes_nome"], 
        y=monthly_rain["precipitacao_total"],
        marker_color="rgba(105,240,174, 0.8)",
        text=monthly_rain["precipitacao_total"].round(0).astype(int).astype(str) + " mm",
        textposition="auto"
    ))
    return _layout(fig, height=260)


def lag_heatmap(df: pd.DataFrame) -> go.Figure:
    monthly = df.resample("ME", on="date").agg(
        ndvi=("ndvi_medio", "mean"),
        chuva=("precipitacao_total", "sum")
    ).dropna()
    monthly["Lag_0"] = monthly["chuva"]
    monthly["Lag_3"] = monthly["chuva"].shift(3)
    monthly["Lag_6"] = monthly["chuva"].shift(6)
    monthly["Lag_9"] = monthly["chuva"].shift(9)
    corr = monthly[["ndvi", "Lag_0", "Lag_3", "Lag_6", "Lag_9"]].corr()
    z = corr[["ndvi"]].drop("ndvi").T
    fig = go.Figure(go.Heatmap(
        z=z.values, x=z.columns.tolist(), y=["Corr NDVI"],
        colorscale="RdYlGn", zmin=-1, zmax=1,
        text=z.values.round(2), texttemplate="%{text}",
        showscale=True,
    ))
    fig.update_layout(height=160, margin=dict(t=10, b=10, l=80, r=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="rgba(180,230,180,.80)")
    return fig


def extreme_events(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["precipitacao_total"],
                             mode="lines", line=dict(color="rgba(100,181,246,.5)", width=1),
                             name="Chuva"))
    extremos = df[df["precipitacao_total"] > 50]
    fig.add_trace(go.Scatter(x=extremos["date"], y=extremos["precipitacao_total"],
                             mode="markers", marker=dict(color="#EF5350", size=7),
                             name=">50mm"))
    fig.add_hline(y=50, line=dict(color="#EF5350", dash="dash", width=1))
    _layout(fig, height=220)
    fig.update_layout(showlegend=True,
                      legend=dict(font=dict(size=9, color="rgba(180,230,180,.70)"),
                                  bgcolor="rgba(0,0,0,0)"))
    return fig
