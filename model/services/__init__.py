import os
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from sklearn.metrics import mean_squared_error, mean_absolute_error


# Model path
MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ppaimodel", "model_rf.joblib"
)

# CSV path
CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", "product", "dataset", "wfp_food_prices_cmr.csv"
)


def load_model():
    """Charge le modèle Random Forest depuis le fichier joblib."""
    try:
        model = joblib.load(MODEL_PATH)
        return model
    except Exception as e:
        print(f"Erreur lors du chargement du modèle: {str(e)}")
        return None


def load_dataframe() -> pd.DataFrame:
    """Charge le CSV du modèle ML."""
    return pd.read_csv(CSV_PATH)

def engineer_features(series: pd.Series) -> pd.DataFrame:
    d = pd.DataFrame({'price': series})

    d['month']      = d.index.month
    d['quarter']    = d.index.quarter
    d['year_norm']  = (d.index.year - d.index.year.min()) / max(1, d.index.year.max() - d.index.year.min())
    d['month_sin']  = np.sin(2 * np.pi * d['month'] / 12)
    d['month_cos']  = np.cos(2 * np.pi * d['month'] / 12)
    d['harvest_main']  = d['month'].isin([7, 8, 9]).astype(int)
    d['harvest_small'] = d['month'].isin([12, 1, 2]).astype(int)

    for lag in [1, 2, 3, 6, 12]:
        d[f'lag_{lag}'] = d['price'].shift(lag)

    for win in [3, 6, 12]:
        shifted = d['price'].shift(1)
        d[f'roll_mean_{win}'] = shifted.rolling(win).mean()
        d[f'roll_std_{win}']  = shifted.rolling(win).std()
        d[f'roll_min_{win}']  = shifted.rolling(win).min()
        d[f'roll_max_{win}']  = shifted.rolling(win).max()

    for p in [1, 3, 6, 12]:
        d[f'pct_change_{p}'] = d['price'].pct_change(p)

    r12 = d['price'].shift(1).rolling(12)
    d['z_score'] = (d['price'] - r12.mean()) / (r12.std() + 1e-8)

    return d.dropna()


def predictprice(commodity: str, date: str, market: str) -> dict | None:
    try:
        model = load_model()
        if model is None:
            return {'status': 'error', 'message': 'Impossible de charger le modèle'}

        df = load_dataframe()
        df['date'] = pd.to_datetime(df['date'])

        # Série temporelle pour ce couple
        ts = (
            df[(df['commodity'] == commodity) & (df['market'] == market)]
            .groupby('date')['price'].mean()
            .resample('MS').mean()
            .interpolate(method='time')
        )

        if len(ts) < 15:
            return {'status': 'error', 'message': f'Pas assez de données pour "{commodity}" @ "{market}"'}

        # Reconstruire les features (MÊME logique que l'entraînement)
        feat_df = engineer_features(ts)
        FEAT_COLS = [c for c in feat_df.columns if c != 'price']

        # Nombre de steps jusqu'à target_date
        last_date = feat_df.index[-1]
        target_dt = pd.to_datetime(date).to_period('M').to_timestamp()
        n_steps   = max(1, (target_dt.year - last_date.year) * 12
                           + (target_dt.month - last_date.month))

        # Prédiction itérative
        last_feat = feat_df.iloc[-1][FEAT_COLS].values.copy()
        pred = None

        for _ in range(n_steps):
            pred = model.predict(last_feat.reshape(1, -1))[0]
            for lag in [12, 6, 3, 2]:
                k = f'lag_{lag}'
                p = f'lag_{lag//2}' if lag > 2 else 'lag_1'
                if k in FEAT_COLS and p in FEAT_COLS:
                    last_feat[FEAT_COLS.index(k)] = last_feat[FEAT_COLS.index(p)]
            if 'lag_1' in FEAT_COLS:
                last_feat[FEAT_COLS.index('lag_1')] = pred
            new_m = (int(last_feat[FEAT_COLS.index('month')]) % 12) + 1
            last_feat[FEAT_COLS.index('month')]     = new_m
            last_feat[FEAT_COLS.index('month_sin')] = np.sin(2 * np.pi * new_m / 12)
            last_feat[FEAT_COLS.index('month_cos')] = np.cos(2 * np.pi * new_m / 12)

        return {
            'product_name':    commodity,
            'date':            date,
            'market':          market,
            'predicted_price': round(float(pred), 2),
            'status':          'success'
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def get_metrics_by_product(commodity: str, market: str) -> dict | None:
    try:
        model = load_model()
        if model is None:
            return {'status': 'error', 'message': 'Impossible de charger le modèle'}

        df = load_dataframe()
        df['date'] = pd.to_datetime(df['date'])

        commodity_data = df[(df['commodity'] == commodity) & (df['market'] == market)].copy()

        if commodity_data.empty:
            return {'status': 'error', 'message': f'Pas de données pour "{commodity}" @ "{market}"'}

        ts = (
            commodity_data.set_index('date')['price']
            .resample('MS').mean()
            .interpolate(method='time')
        )
        feat_df   = engineer_features(ts)
        FEAT_COLS = [c for c in feat_df.columns if c != 'price']
        X         = feat_df[FEAT_COLS]
        y         = feat_df['price'].values
        y_pred    = model.predict(np.array(X))

        rmse = np.sqrt(mean_squared_error(y, y_pred))
        mae  = mean_absolute_error(y, y_pred)
        mape = np.mean(np.abs((y - y_pred) / (y + 1e-8))) * 100

        return {
            'commodity':   commodity,
            'market':      market,
            'rmse':        round(float(rmse), 2),
            'mae':         round(float(mae), 2),
            'mape':        round(float(mape), 2),
            'num_samples': len(feat_df),
            'status':      'success'
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}