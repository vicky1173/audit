"""UI theme: dark/light mode CSS and glassmorphism styling."""

DARK_THEME = {
    "bg_primary": "#0a0e17",
    "bg_secondary": "#111827",
    "bg_card": "rgba(17, 24, 39, 0.75)",
    "bg_glass": "rgba(255, 255, 255, 0.05)",
    "text_primary": "#f9fafb",
    "text_secondary": "#9ca3af",
    "accent": "#3b82f6",
    "accent_gradient": "linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "border": "rgba(255, 255, 255, 0.1)",
    "chart_bg": "#111827",
}

LIGHT_THEME = {
    "bg_primary": "#f3f4f6",
    "bg_secondary": "#ffffff",
    "bg_card": "rgba(255, 255, 255, 0.85)",
    "bg_glass": "rgba(255, 255, 255, 0.6)",
    "text_primary": "#111827",
    "text_secondary": "#6b7280",
    "accent": "#2563eb",
    "accent_gradient": "linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)",
    "success": "#059669",
    "warning": "#d97706",
    "danger": "#dc2626",
    "border": "rgba(0, 0, 0, 0.08)",
    "chart_bg": "#ffffff",
}


def get_theme_css(theme: dict) -> str:
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    .stApp {{
        background: {theme['bg_primary']};
        color: {theme['text_primary']};
    }}

    [data-testid="stSidebar"] {{
        background: {theme['bg_secondary']} !important;
        border-right: 1px solid {theme['border']};
    }}

    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {{
        color: {theme['text_primary']};
    }}

    .glass-card {{
        background: {theme['bg_glass']};
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid {theme['border']};
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
    }}

    .kpi-card {{
        background: {theme['bg_card']};
        backdrop-filter: blur(12px);
        border: 1px solid {theme['border']};
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}

    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(59, 130, 246, 0.15);
    }}

    .kpi-value {{
        font-size: 2rem;
        font-weight: 800;
        background: {theme['accent_gradient']};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    .kpi-label {{
        font-size: 0.85rem;
        color: {theme['text_secondary']};
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }}

    .kpi-delta {{
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }}

    .risk-low {{ color: {theme['success']}; }}
    .risk-medium {{ color: {theme['warning']}; }}
    .risk-high {{ color: #f97316; }}
    .risk-critical {{ color: {theme['danger']}; }}

    .header-banner {{
        background: {theme['accent_gradient']};
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        color: white;
    }}

    .header-banner h1 {{
        margin: 0;
        font-size: 1.75rem;
        font-weight: 700;
    }}

    .header-banner p {{
        margin: 0.25rem 0 0 0;
        opacity: 0.9;
        font-size: 0.95rem;
    }}

    .section-title {{
        font-size: 1.1rem;
        font-weight: 600;
        color: {theme['text_primary']};
        border-left: 4px solid {theme['accent']};
        padding-left: 0.75rem;
        margin: 1.5rem 0 1rem 0;
    }}

    .login-container {{
        max-width: 420px;
        margin: 4rem auto;
        padding: 2.5rem;
        background: {theme['bg_card']};
        backdrop-filter: blur(20px);
        border: 1px solid {theme['border']};
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
    }}

    .login-title {{
        text-align: center;
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }}

    .login-subtitle {{
        text-align: center;
        color: {theme['text_secondary']};
        font-size: 0.85rem;
        margin-bottom: 1.5rem;
    }}

    div[data-testid="stMetric"] {{
        background: {theme['bg_card']};
        border: 1px solid {theme['border']};
        border-radius: 12px;
        padding: 1rem;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}

    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px;
        padding: 8px 16px;
    }}

    .audit-module-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 1rem 0 1.5rem 0;
        border: 1px solid #dbeafe;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 24px rgba(30, 58, 95, 0.08);
    }}

    .audit-module-table th {{
        background: linear-gradient(135deg, #1e3a5f 0%, #1e40af 100%);
        color: #ffffff;
        font-weight: 700;
        text-align: left;
        padding: 0.85rem 1rem;
        font-size: 0.9rem;
        letter-spacing: 0.02em;
    }}

    .audit-module-table td {{
        padding: 0.75rem 1rem;
        border-top: 1px solid #e5e7eb;
        vertical-align: top;
        font-size: 0.9rem;
        line-height: 1.5;
    }}

    .audit-module-table tr:nth-child(even) td {{
        background: rgba(219, 234, 254, 0.35);
    }}

    .audit-module-table tr:nth-child(odd) td {{
        background: rgba(248, 250, 252, 0.9);
    }}

    .audit-module-id {{
        font-weight: 800;
        color: #1e3a8a;
        font-size: 1.1rem;
        white-space: nowrap;
        width: 56px;
    }}

    .audit-module-title {{
        font-weight: 700;
        color: #1e3a8a;
        min-width: 180px;
    }}

    .audit-module-item {{
        color: {theme['text_primary']};
        padding: 0.35rem 0;
        border-bottom: 1px dashed rgba(148, 163, 184, 0.4);
    }}

    .audit-module-item:last-child {{
        border-bottom: none;
    }}

    .hero-stats {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 0.75rem;
        margin-top: 1rem;
    }}

    .hero-stat {{
        background: rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        text-align: center;
    }}

    .hero-stat-value {{
        font-size: 1.5rem;
        font-weight: 800;
    }}

    .hero-stat-label {{
        font-size: 0.75rem;
        opacity: 0.85;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}

    [data-testid="stFileUploader"] section {{
        border: 1px dashed {theme['border']};
        border-radius: 12px;
        padding: 0.5rem;
    }}

    div[data-testid="stDataFrame"] {{
        border: 1px solid {theme['border']};
        border-radius: 12px;
        overflow: hidden;
    }}
    </style>
    """
