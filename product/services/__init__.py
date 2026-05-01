import os
import pandas as pd

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "dataset", "wfp_food_prices_cmr.csv"
)

def load_dataframe() -> pd.DataFrame:
    """Charge le CSV du modèle ML."""
    return pd.read_csv(CSV_PATH)

def get_all_products() -> list[dict]:
    """
    Retourne la liste dédupliquée de tous les produits
    avec leur commodity_id et market_id.
    """
    try:
        df = load_dataframe()
        products = (
            df[["commodity_id", "commodity", "market_id", "market"]]
            .drop_duplicates(subset=["commodity_id", "market_id"])
            .rename(columns={
                "commodity_id": "id",
                "commodity": "name",
                "market_id": "market_id",
                "market": "market_name",
            })
            .sort_values("id")
            .to_dict(orient="records")
        )
        return products
    except Exception:
        return []

def get_product_by_id(product_id: int) -> dict | None:
    """
    Retourne le premier produit correspondant au commodity_id donné,
    ou None s'il n'existe pas.
    """
    try:
        df = load_dataframe()
        match = df[df["commodity_id"] == product_id]
        if match.empty:
            return None
        row = (
            match[["commodity_id", "commodity", "market_id", "market"]]
            .drop_duplicates(subset=["commodity_id"])
            .rename(columns={
                "commodity_id": "id",
                "commodity": "name",
                "market_id": "market_id",
                "market": "market_name",
            })
            .iloc[0]
            .to_dict()
        )
        return row
    except Exception:
        return None

def get_products_by_market(market_id: int) -> list[dict]:
    """
    Retourne tous les produits disponibles dans un marché donné
    (filtre sur market_id, dédupliqué par commodity_id).
    """
    try:
        df = load_dataframe()
        match = df[df["market_id"] == market_id]
        if match.empty:
            return []
        products = (
            match[["commodity_id", "commodity", "market_id", "market"]]
            .drop_duplicates(subset=["commodity_id"])
            .rename(columns={
                "commodity_id": "id",
                "commodity": "name",
                "market_id": "market_id",
                "market": "market_name",
            })
            .sort_values("id")
            .to_dict(orient="records")
        )
        return products
    except Exception:
        return []