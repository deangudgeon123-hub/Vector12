# ClinicalTrials.gov import

Vector12 imports public study records from the ClinicalTrials.gov API v2 by NCT identifier.

The importer currently normalises:

- NCT identifier
- brief and official title
- lead sponsor
- phase
- recruitment status
- study type
- minimum and maximum age
- sex
- eligibility criteria text
- canonical ClinicalTrials.gov source URL

The importer deliberately does not write directly to the Vector12 database yet.
Database writes remain blocked by Row Level Security until a server-side Supabase
service-role secret is configured for the Railway backend.

This keeps the current default-deny database posture intact while allowing the
trial ingestion and eligibility compilation pipeline to be developed and tested.
