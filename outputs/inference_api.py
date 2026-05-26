
from flask import Flask, request, jsonify
import xgboost as xgb
import numpy as np
import pickle, json

app = Flask(__name__)

MODEL_PATH   = "../outputs/models/xgb_train18238.json"
FEAT_PATH    = "../outputs/models/feature_columns.json"
MEDIAN_PATH  = "../outputs/models/median_imputer.pkl"
STD_PATH     = "../outputs/models/station_residual_std.pkl"

model = xgb.Booster(); model.load_model(MODEL_PATH)
with open(FEAT_PATH) as f:  feature_cols = json.load(f)["features"]
with open(MEDIAN_PATH, "rb") as f:  medians = pickle.load(f)
with open(STD_PATH, "rb") as f:  station_std = pickle.load(f)

@app.route("/predict-delay", methods=["POST"])
def predict_delay():
    body = request.get_json(force=True)
    prev = body.get("previous_delays", [])
    row = {c: medians.get(c, 0) for c in feature_cols}
    row["current_delay"]            = body.get("current_delay", 0)
    row["previous_delay_1"]         = prev[-1] if len(prev) >= 1 else row["current_delay"]
    row["previous_delay_2"]         = prev[-2] if len(prev) >= 2 else row["previous_delay_1"]
    row["station_index"]            = body.get("station_index", 0)
    row["day_of_week"]              = body.get("day_of_week", 0)
    row["month"]                    = body.get("month", 1)
    row["hour_of_day"]              = body.get("hour_of_day", 12)
    row["rolling_avg_last_3_delays"] = np.mean([row["current_delay"],
                                                  row["previous_delay_1"],
                                                  row["previous_delay_2"]])
    feat = np.array([[row[c] for c in feature_cols]])
    dm   = xgb.DMatrix(feat, feature_names=feature_cols)
    pred = float(model.predict(dm)[0])
    s_idx = int(body.get("station_index", 0))
    std  = station_std.get(s_idx, np.std(list(station_std.values())))
    return jsonify({
        "next_station_delay": round(pred, 2),
        "confidence_range": [round(pred - 1.5*std, 2), round(pred + 1.5*std, 2)]
    })

if __name__ == "__main__":
    app.run(port=5001, debug=False)
