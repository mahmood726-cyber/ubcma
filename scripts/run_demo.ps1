$env:PYTHONPATH = "src"
python -m ubcma fit examples\toy_studies.csv --quality rob_selection,rob_measurement,rob_reporting --moderators moderator --design design --design-reference RCT --study-id study_id
