import json
from pathlib import Path
from django.apps import apps

# ======= CONFIG: We can configure this. =======
JSON_PATH = Path("careers.json")
APP_LABEL = "programs"
# ====================================

Program = apps.get_model(APP_LABEL, "Program")
JobPosition = apps.get_model(APP_LABEL, "JobPosition")

# Resolve JSON
if not JSON_PATH.is_absolute():
    JSON_PATH = (Path.cwd() / JSON_PATH).resolve()

if not JSON_PATH.exists():
    raise FileNotFoundError(f"JSON not found at: {JSON_PATH}")

data = json.load(open(JSON_PATH, "r", encoding="utf-8"))

added_programs = 0
skipped_programs = 0
not_found_programs = 0
multi_match_programs = 0

for item in data:
    plan = item.get("degree_plan_code")
    subplan = item.get("degree_subplan_code")
    careers = item.get("careers") or []

    # Find the Program
    qs = Program.objects.filter(plan_code=plan)
    qs = qs.filter(subplan_code__isnull=True) if subplan is None else qs.filter(subplan_code=subplan)
    count = qs.count()

    if count == 0:
        print(f"X Program not found: plan={plan}, subplan={subplan}")
        not_found_programs += 1
        continue

    program = qs.first()

    # Skip if program already has jobs
    if program.jobs.exists():
        print(f">> Skipping '{program.name}' (already has jobs)")
        skipped_programs += 1
        continue

    # Create/link jobs
    jobs_to_add = []
    for name in set(careers):
        job, created = JobPosition.objects.get_or_create(name=name)
        jobs_to_add.append(job)

    if jobs_to_add:
        program.jobs.add(*jobs_to_add)
        print(f"+ Linked {len(jobs_to_add)} jobs to '{program.name}' (plan={plan}, subplan={subplan})")
        added_programs += 1

print("\n*** Import Report ***")
print(f"Programs updated with jobs: {added_programs}")
print(f"Programs skipped (already had jobs): {skipped_programs}")
print(f"Programs not found: {not_found_programs}")
print(f"Total processed from JSON: {len(data)}")
print(f"JSON used: {JSON_PATH}")
