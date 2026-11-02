#!/bin/sh
# Read-only identity-gate values for KOBO-001 in database $1, dates relative to the story S ($2, YYYY-MM-DD).
DB=$1; S=$2
q() { docker exec assetopsv1-postgres-1 psql -U assetops -d "$DB" -AtF' | ' -c "$1"; }
SITE="(select id from site where site_code='KOBO-001')"
echo "== verification outcome"
q "select outcome, reasons, (details->'windows'->'baseline') - 'window_start' - 'window_end', (details->'windows'->'later') - 'window_start' - 'window_end', details->'target'->'baseline_seconds', details->'target'->'later'->'candidate_seconds', details->'comparability'->'bands' from verification_outcome where site_id=$SITE order by recorded_at desc limit 1"
echo "== verification metrics"
q "select metric_key, window_name, state, value_text, threshold_text, unit from verification_metric where outcome_id=(select id from verification_outcome where site_id=$SITE order by recorded_at desc limit 1) order by 1,2"
echo "== trial cost check"
q "select state, reason, ((((result - 'plan_id' - 'outcome_id') #- '{price,revision_id}') - 'origin_finding_revision_id') - 'recorded_at' - 'evidence_ids' - 'basis_sha256')::text, intervention_cost::text from trial_cost_comparison_revision where site_id=$SITE order by recorded_at desc, revision_no desc limit 1"
echo "== dispatch assessments (day offset from S, analytic, claim, minute fields)"
q "select (window_start at time zone 'Africa/Addis_Ababa')::date - date '$S', analytic_id, claim_level, (select string_agg(k||'='||(result->>k), ',' order by k) from jsonb_object_keys(result) k where k ilike '%minute%' or k ilike '%avoidable%' or k ilike '%unclear%') from assessment_revision a where site_id=$SITE and revision_no=(select max(revision_no) from assessment_revision b where b.site_id=a.site_id and b.assessment_key=a.assessment_key) order by 1,2"
echo "== financial consequences (day offset, type, state, quantity, amount)"
q "select (window_start at time zone 'Africa/Addis_Ababa')::date - date '$S', consequence_type, state, quantity_state, quantity_low, quantity_high, amount_low, amount_high, currency from financial_consequence_revision a where site_id=$SITE and revision_no=(select max(revision_no) from financial_consequence_revision b where b.finding_id=a.finding_id and b.consequence_type=a.consequence_type) order by 1,2"
