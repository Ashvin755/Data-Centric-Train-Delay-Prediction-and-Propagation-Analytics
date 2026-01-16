# Rail Delay Dataset Collection – Updated System Spec

## 1. Objective

Build a reliable **Indian Railways train delay dataset** for an ML-based delay prediction project by periodically polling RailRadar APIs and persisting journey- and station-level data in Supabase.

---

## 2. Core Definitions

### Journey Date

**`journey_date` = the calendar date on which the train departs from its source station.**

* It is **not** the polling date.
* Multi-day journeys retain the same `journey_date` across all polling cycles.
* Daily-running trains may have **multiple parallel journeys** (one per calendar day).

---

## 3. Train Categorization

Trains are pre-classified in `train_info`.

| Category       | Criteria               | Handling                 |
| -------------- | ---------------------- | ------------------------ |
| `one_day`      | Journey duration ≤ 24h | Higher polling frequency |
| `multiple_day` | Journey duration > 24h | Lower polling frequency  |

Each category uses:

* A **separate Render endpoint**
* A **separate RailRadar API key**
* A **shared Supabase database**

---

## 4. Deployment Architecture

### Hosting

* Python services hosted on **Render (Free tier)**.
* Services are **stateless**.

### Scheduling

* Polling triggered by an **external uptime/cron service** (e.g. UptimeRobot).

### Endpoints

* `/poll/one-day`
* `/poll/multi-day`

Flow:
`Uptime Monitor → Render Endpoint → RailRadar API → Supabase`

---

## 5. Polling Strategy

| Journey Type | Poll Interval | RailRadar dataType |
| ------------ | ------------- | ------------------ |
| One-day      | ~5 hours      | `live`             |
| Multi-day    | ~12 hours     | `live`             |

Notes:

* `journeyDate` is always passed explicitly.
* `dataType=live` is used to minimize payload and API usage.

---

## 6. State Management Tables

### `train_info`

* Static train metadata
* Journey classification (`one_day`, `multiple_day`)

### `journey_status_flags`

Controls lifecycle of each journey `(train_no, journey_date)`.

Key columns:

* `flag` – poll attempt counter
* `is_completed` – journey successfully completed
* `is_abandoned` – journey stopped after exceeding poll threshold
* `last_checked_at`

### `rail_data`

* Final immutable dataset
* One row per `(train_no, journey_date, station_code)`

---

## 7. Journey Lifecycle Logic

Each `(train_no, journey_date)` behaves as a state machine:

```
NEW → IN_PROGRESS → COMPLETED
        ↓
     ABANDONED
```

Once a journey becomes **COMPLETED** or **ABANDONED**, it is never polled again.

---

## 8. Poll Execution Logic (Updated)

Each poll run executes **two independent workflows in parallel**.

---

### A. New Journeys Starting Today

For each train in `train_info`:

1. Set:

   ```
   candidate_journey_date = today (IST)
   ```

2. Check `journey_status_flags` for `(train_no, candidate_journey_date)`.

3. If a row exists → **skip**.

4. If no row exists:

   * Call RailRadar with:

     ```
     trainNumber = X
     journeyDate = candidate_journey_date
     dataType = live
     ```

5. If RailRadar confirms the train **started today**:

   * Insert into `journey_status_flags`:

     ```
     train_no = X
     journey_date = today
     flag = 0
     is_completed = false
     is_abandoned = false
     ```

6. If RailRadar indicates the train did **not** start today → do nothing.

---

### B. Ongoing Incomplete Journeys

Fetch all journeys where:

```
is_completed = false
AND is_abandoned = false
```

For each `(train_no, journey_date)`:

1. Call RailRadar with:

   ```
   trainNumber = X
   journeyDate = journey_date
   dataType = live
   ```

2. Determine completion using:

   ```
   liveData.currentLocation.stationCode
   == train_info.destination_station_code
   ```

3. If **completed**:

   * Extract `liveData.route`
   * Insert station-level rows into `rail_data`
   * Update `journey_status_flags`:

     ```
     is_completed = true
     ```

4. If **not completed**:

   * Increment `flag`
   * Update `last_checked_at`

5. If:

   ```
   flag > max_flag_threshold
   AND is_completed = false
   ```

   then:

   ```
   is_abandoned = true
   ```

Abandoned journeys are **never polled again** and produce **no rows** in `rail_data`.

---

## 9. Parallel Journey Handling

* The same train number can have **multiple active journeys** at once.
* Example on Jan 16:

| train_no | journey_date | Reason                    |
| -------- | ------------ | ------------------------- |
| X        | Jan 15       | Ongoing multi-day journey |
| X        | Jan 16       | New daily run             |

Each journey is tracked independently via `(train_no, journey_date)`.

---

## 10. Data Ingestion Scope

Primary fields used from RailRadar:

* `liveData.route[]`

  * stationCode
  * scheduledArrival / scheduledDeparture
  * actualArrival / actualDeparture
  * delayArrivalMinutes / delayDepartureMinutes
  * distanceFromOriginKm

* `liveData.currentLocation.stationCode` (completion check)

---

## 11. Constraints & Limits

* RailRadar API limit: **1000 calls/month per API key**
* Render Free tier:

  * No native cron
  * Time-limited executions

Mitigations:

* Separate API keys per journey type
* Different polling intervals
* Abandonment via flag threshold

---

## 12. Known Design Trade-offs

* Abandoned journeys may later complete, but are intentionally skipped.
* This introduces **selection bias**, which must be documented in the ML project.
* Historical backfill is out of scope.

---

## 13. Success Criteria

* No duplicate station rows
* Deterministic journey lifecycle
* API usage within limits
* Clean separation between state control and dataset

---

This spec reflects the updated logic with `is_abandoned` and is implementation-ready.
