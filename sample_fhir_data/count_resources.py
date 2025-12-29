#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
bundle_file = os.path.join(script_dir, "patient_complete_bundle.json")

with open(bundle_file, 'r', encoding='utf-8') as f:
    bundle = json.load(f)

entries = bundle.get('entry', [])
resources = {}
patients = set()
exams = set()

for entry in entries:
    resource = entry.get('resource', {})
    resource_type = resource.get('resourceType', 'Unknown')
    resource_id = resource.get('id', '')
    
    resources[resource_type] = resources.get(resource_type, 0) + 1
    
    if resource_type == 'Patient':
        patients.add(resource_id)
    elif resource_type == 'ServiceRequest':
        exams.add(resource_id)

print("Patients:", sorted(patients))
print("ServiceRequests:", sorted(exams))
print("\nResource counts:")
for k, v in sorted(resources.items()):
    print(f"  {k}: {v}")



