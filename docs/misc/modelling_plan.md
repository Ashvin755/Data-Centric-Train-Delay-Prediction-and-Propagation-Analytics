# 🚆 Railway Delay Prediction System — Multi-Phase ML Development Plan

# Project Goal

Build train-specific ML models that predict future station delays for a running train using historical journey data.

Each model should:

* learn delay propagation behavior,
* understand train-specific operational patterns,
* predict upcoming delays station-by-station,
* and integrate into the analytics dashboard.

Target:

* Initially build models for 2 trains only.
* Later scale architecture for additional trains.

---

# 🧠 Core ML Problem Definition

## Problem Type

Sequential operational forecasting.

## Input

Delays/timing data from previous stations in the current journey.

## Output

Predicted delay at the next station (use delay_departure_minutes).

---

# Overall Architecture

```text
Historical Journeys
        ↓
Feature Engineering Pipeline
        ↓
Training Dataset Generation
        ↓
Baseline Models
        ↓
XGBoost Model
        ↓
LSTM / TCN Advanced Model
        ↓
Prediction APIs
        ↓
Dashboard Visualization
```

---

# PHASE 1 — DATASET & FEATURE ENGINEERING PIPELINE

# Objective

Create a robust ML-ready dataset from raw railway journey data.

This is the MOST important phase.

Poor feature engineering = poor models.

---

# Step 1.1 — Create Clean Modeling Dataset

## Tasks

* Load station-level rail_data table
* Sort rows by:

  * train_no
  * journey_date
  * station sequence
* Remove duplicates
* Handle missing delays/timestamps
* Validate station order consistency

## Output

Clean chronological station-level dataset.

---

# Step 1.2 — Build Station Sequence Mapping

## Goal

Create stable station ordering for each train.

## Tasks

For each train:

* use the static JSON route and keep halt-only stations as the canonical route
* assign station_index:

        * source = 0
        * next station = 1
        * etc.

## Example

```text
NDLS → 0
BPL → 1
NGP → 2
HYB → 3
```

## Output

station_index mapping table.

---

# Step 1.3 — Generate Journey Training Rows

## Goal

Convert journeys into supervised ML rows.

## Transformation Logic

For station i:
predict station i+1 delay_departure_minutes.

## Example

Input:

```text
Current station: BPL
Current delay: 18
Previous delay: 10
Station index: 5
```

Target:

```text
Next station delay: 31
```

---

# Step 1.4 — Create Core Features

# A. Current-State Features

## Required

* current_delay
* previous_delay_1
* previous_delay_2
* station_index
* distance_from_origin
* journey_progress_percentage

---

# B. Temporal Features

## Required

* hour_of_day
* day_of_week
* is_weekend
* month
* overnight_segment_flag

---

# C. Segment Features

## Required

* distance_to_next_station
* scheduled_travel_time
* halt_duration
* average_speed_expected

---

# D. Historical Statistical Features

## Required

* avg_delay_at_station (expanding window, past-only)
* avg_delay_on_segment (expanding window, past-only)
* avg_delay_for_train (expanding window, past-only)
* station_congestion_score (expanding window, past-only)
* delay_variance_at_station (expanding window, past-only)

These features are HIGH VALUE but must be computed without leakage.

---

# E. Rolling Sequence Features

## Required

* rolling_avg_last_3_delays
* rolling_std_last_3_delays
* delay_trend_slope

---

# Step 1.5 — Feature Validation

## Tasks

* detect nulls
* check feature ranges
* validate chronological consistency
* validate target generation

## Deliverables

* feature summary report
* null percentage report
* sample training rows

---

# Step 1.6 — Dataset Splitting Strategy

# IMPORTANT

Use:

# TIME-BASED SPLIT ONLY

## Example

```text
Train:
Jan → Mar → Training
Apr → Validation
May → Test
```

DO NOT randomly shuffle.

Reason:
Avoid future leakage.

---

# Step 1.7 — Save ML Datasets

## Output Files

```text
train_XXXXX_train.csv
train_XXXXX_val.csv
train_XXXXX_test.csv
```

Also save:

* scaler objects
* feature list
* metadata

---

# PHASE 2 — BASELINE & LINEAR MODELS

# Objective

Create simple benchmark models.

These establish:

* minimum expected performance,
* and prove ML value.

---

# Step 2.1 — Persistence Baseline

# Model Logic

```python
predicted_next_delay = current_delay
```

---

# Why Important

Railway delays are highly persistent.

If ML cannot beat this:
the ML pipeline is weak.

---

# Metrics

Evaluate:

* MAE
* RMSE

---

# Step 2.2 — Moving Average Baseline

## Logic

```python
prediction =
average(last_2_or_3_delays)
```

---

# Step 2.3 — Linear Regression Model

## Features

Use:

* delays
* station index
* temporal features
* distance features

---

# Goals

* establish interpretable benchmark
* identify major coefficients
* validate feature usefulness

---

# Step 2.4 — Ridge Regression

## Why

Handle multicollinearity and stabilize coefficients.

---

# Step 2.5 — Baseline Evaluation Framework

## Create Common Evaluation Pipeline

For every model:

* train
* predict
* evaluate
* save metrics
* save plots

---

# Required Metrics

## Primary

* MAE

## Secondary

* RMSE
* R² (optional)

---

# Required Visualizations

## Generate

* actual vs predicted
* residual plot
* delay distribution
* prediction error histogram

---

# Step 2.6 — Baseline Analysis Report

## Compare

| Model             | MAE | RMSE |
| ----------------- | --- | ---- |
| Persistence       |     |      |
| Moving Average    |     |      |
| Linear Regression |     |      |
| Ridge Regression  |     |      |

---

# PHASE 3 — XGBOOST MODEL (MAIN MODEL)

# Objective

Build high-performance production-grade predictor.

This becomes:

# the main deployed model.

---

# Step 3.1 — Setup XGBoost Pipeline

## Tasks

* install xgboost
* create reusable training pipeline
* define feature schema

---

# Step 3.2 — Initial Model Training

## Start Simple

Basic params:

```python
max_depth=6
learning_rate=0.05
n_estimators=300
subsample=0.8
```

---

# Step 3.3 — Hyperparameter Tuning

## Tune

* max_depth
* learning_rate
* min_child_weight
* subsample
* colsample_bytree

Use:

* GridSearchCV
  OR
* Optuna

---

# Step 3.4 — Feature Importance Analysis

## Generate

* gain importance
* SHAP values
* top contributing features

---

# Deliverables

## Dashboard Insights

```text
Most influential factors:
1. Current delay
2. Station index
3. Halt duration
```

VERY valuable academically.

---

# Step 3.5 — Recursive Multi-Station Prediction

# Goal

Predict remaining journey delays.

---

# Logic

Predict:

```text
station i+1
```

Then feed prediction into:

```text
station i+2
```

Continue recursively.

---

# Step 3.6 — Prediction Confidence Estimation

## Methods

Option 1:
Residual std deviation.

Option 2:
Quantile regression.

---

# Output Example

```text
Expected final delay:
42 ± 8 mins
```

---

# Step 3.7 — Error Analysis

## Analyze

* worst predictions
* station-specific failures
* night-time performance
* long-delay scenarios

---

# Step 3.8 — Model Serialization

## Save

```text
model.pkl
feature_columns.json
scaler.pkl
```

---

# Step 3.9 — Flask Inference API

# Endpoint

```text
POST /predict-delay
```

---

# Input

```json
{
        "train_no": 12627,
        "current_station": "BPL",
        "current_delay": 18,
        "previous_delays": [12, 10],
        "station_index": 5,
        "distance_from_origin": 530.0,
        "hour_of_day": 14,
        "day_of_week": 2,
        "month": 5
}
```

---

# Output

```json
{
  "next_station_delay": 31,
  "confidence_range": [24, 38]
}
```

---

# Step 3.10 — Dashboard Integration

## Required Widgets

* predicted delay curve
* actual vs predicted
* delay propagation graph
* confidence interval visualization

---

# PHASE 4 — ADVANCED SEQUENCE MODELS (LSTM / TCN)

# Objective

Experiment with true sequence-learning models.

This is:

* advanced phase,
* and research-oriented enhancement.

NOT primary production model initially.

---

# Recommended Order

# First:

TCN

# Then:

LSTM

Reason:
TCNs are:

* easier to train,
* more stable,
* often outperform LSTMs on structured sequences.

---

# Step 4.1 — Sequence Dataset Generation

## Input Format

Split by time first, then generate sliding windows within each split.

---

# Example

Input:

```text
[0, 5, 12, 18]
```

Output:

```text
31
```

---

# Step 4.2 — Sequence Tensor Creation

## Convert Into

```python
(samples, sequence_length, features)
```

---

# Step 4.3 — Train TCN Model

## Architecture

* causal convolutions
* dilation layers
* residual blocks

---

# Why TCN First

Advantages:

* parallel training
* stable gradients
* lower memory usage
* excellent sequence learning

---

# Step 4.4 — Train LSTM Model

## Architecture

* stacked LSTM
* dropout
* dense output layer

---

# Step 4.5 — Compare Sequence Models

## Compare Against

| Model             | MAE |
| ----------------- | --- |
| Persistence       |     |
| Linear Regression |     |
| XGBoost           |     |
| TCN               |     |
| LSTM              |     |

---

# Step 4.6 — Sequence Visualization

## Dashboard Features

* predicted delay trajectory
* actual sequence replay
* sequence attention visualization (optional)

---

# Step 4.7 — Final Comparative Analysis

# Key Questions

* Does deep learning outperform XGBoost?
* Is additional complexity justified?
* Does sequence learning improve long-range forecasting?

---

# PHASE 5 — PRODUCTIONIZATION & DASHBOARD AI FEATURES

# Objective

Integrate ML system into railway intelligence dashboard.

---

# Step 5.1 — Real-Time Prediction Pipeline

## Flow

```text
Live Journey Data
        ↓
Feature Builder
        ↓
Model Inference
        ↓
Prediction API
        ↓
Dashboard
```

---

# Step 5.2 — Journey Forecast Visualization

## Features

* predicted delay curve
* route progression
* delay buildup visualization
* future station predictions

---

# Step 5.3 — Train Reliability Scoring

## Formula

Based on:

* avg delay
* delay variance
* recovery behavior
* severe delay frequency

---

# Step 5.4 — Delay Propagation Analytics

## Detect

* bottleneck stations
* delay amplification segments
* recovery segments

---

# Step 5.5 — AI Insight Generation

## Examples

```text
This train usually accumulates delay after Nagpur.

High likelihood of delay recovery before Hyderabad.
```

Can initially be rule-based.

---

# FINAL PROJECT DELIVERABLES

# ML Deliverables

* cleaned datasets
* feature engineering pipeline
* baseline models
* XGBoost predictor
* TCN/LSTM experimental models
* evaluation framework

---

# Backend Deliverables

* prediction APIs
* model serialization
* inference pipeline

---

# Dashboard Deliverables

* live prediction panels
* delay evolution visualization
* confidence intervals
* reliability analytics
* route intelligence

---

# IMPORTANT ENGINEERING PRINCIPLES

# DO NOT:

* over-engineer early
* start with deep learning
* skip baselines
* use random train/test split
* compute historical stats using future data

---

# DO:

* validate every phase independently
* save intermediate datasets
* log all experiments
* track metrics consistently
* build reusable pipelines
* compute historical stats using expanding windows on past-only data

---

# RECOMMENDED DEVELOPMENT ORDER

# STRICT EXECUTION ORDER

## 1.

Data cleaning

## 2.

Feature engineering

## 3.

Persistence baseline

## 4.

Linear regression

## 5.

XGBoost

## 6.

Recursive forecasting

## 7.

Dashboard integration

## 8.

TCN

## 9.

LSTM

---

# FINAL RECOMMENDATION

For your current project:

# XGBoost should be the primary production model.

TCN/LSTM should be:

* research comparison models,
* not initial deployment models.

This gives:

* strong academic depth,
* practical engineering quality,
* explainability,
* and an impressive final demo.
