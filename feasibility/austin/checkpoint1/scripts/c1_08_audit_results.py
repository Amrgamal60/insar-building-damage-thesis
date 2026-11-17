"""Checkpoint 1 (AUSTIN_PLAN §4 label audit; §5 demolition audit): results of the hand reading.

The samples were drawn by c1_07_audit_samples_demolition_checks.py (seeds 2028 and 2036).
Each sampled description was read once by Claude (an AI model), from the permit text only,
on 2026-11-10. No engineer and no second reader checked the classes. The classes below were
entered by hand; this script checks them against the private samples and computes the shares
with exact (Clopper-Pearson) 95% intervals, as in the readiness check.

Label classes (feasibility/candidates/austin_a4_classes.json): REPAIR_EXISTING_FOUNDATION,
NEW_CONSTRUCTION, NOT_FOUNDATION, UNCLEAR. Precision = REPAIR_EXISTING_FOUNDATION / 100.
Demolition classes: MAIN_HOUSE (the permit demolishes the single-family house), ACCESSORY_ONLY
(a garage, shed, carport, pool, deck or second unit; the house is not named), UNCLEAR.

The project files carry the permit number, the class and a reason in the reader's words.
No description, name or address is written to the project.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
from scipy.stats import beta

p = argparse.ArgumentParser()
p.add_argument("--audits-private", type=Path, required=True)
p.add_argument("--samples-json", type=Path, required=True)
p.add_argument("--out-dir", type=Path, required=True)
a = p.parse_args()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cp(k, n):
    lo = 0.0 if k == 0 else float(beta.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(0.975, k + 1, n - k))
    return dict(count=int(k), denominator=int(n), percent=round(100 * k / n, 1),
                clopper_pearson_95=[round(100 * lo, 1), round(100 * hi, 1)])


R = "REPAIR_EXISTING_FOUNDATION"
PLAIN = "Foundation repair of an existing house."
PIERS = "Foundation repair with a stated number of piers or pilings."
PIERS_ONLY = "Piers installed under an existing house; the text does not use the word repair."
MIXED = "Foundation repair listed with other repair or remodel work."
LABEL_EXCEPTIONS = {
    "L012": (R, PIERS_ONLY), "L024": (R, PIERS_ONLY), "L092": (R, PIERS_ONLY), "L100": (R, PIERS_ONLY),
    "L026": (R, PIERS), "L028": (R, PIERS), "L031": (R, PIERS), "L032": (R, PIERS), "L038": (R, PIERS),
    "L043": (R, PIERS), "L044": (R, PIERS), "L046": (R, PIERS), "L055": (R, PIERS), "L063": (R, PIERS),
    "L064": (R, PIERS), "L073": (R, PIERS), "L091": (R, PIERS), "L095": (R, PIERS), "L097": (R, PIERS),
    "L015": (R, MIXED), "L034": (R, MIXED), "L048": (R, MIXED), "L060": (R, MIXED), "L065": (R, MIXED),
    "L066": (R, MIXED), "L067": (R, MIXED), "L068": (R, MIXED), "L089": (R, MIXED),
    "L035": (R, "Adjustment of existing piers, which implies an earlier repair that is not in the record."),
    "L017": ("UNCLEAR", "The foundation is named in a long list of remodel work without a clear repair statement."),
    "L084": ("NOT_FOUNDATION", "Fire-damage repair of a detached garage; the foundation is mentioned only as unable to carry a rebuild."),
}
M, A = "MAIN_HOUSE", "ACCESSORY_ONLY"
HOUSE = "Total demolition of the single-family house."
DEMOLITION_EXCEPTIONS = {
    "D002": (A, "Detached garage."), "D005": (A, "Pool; the text says the home remains."), "D013": (A, "Detached garage."),
    "D020": (A, "Detached garage."), "D027": (A, "Wood deck and above-ground pool."), "D028": (A, "Detached structure."),
    "D029": (A, "Second unit only."), "D034": (A, "Shed."), "D037": (A, "Detached garage and storage structure."),
    "D042": (A, "Detached carport."), "D043": (A, "Pool."), "D050": (A, "Detached garage."),
    "D004": (M, "Total demolition of the single-family house and a detached accessory structure."),
    "D047": (M, "Total demolition of the single-family house and a detached garage."),
}

S = json.loads(a.samples_json.read_text())
out = {}
for name, sample, default, exceptions, positive in (
        ("label_audit", "label_audit_sample.csv", (R, PLAIN), LABEL_EXCEPTIONS, R),
        ("demolition_audit", "demolition_audit_sample.csv", (M, HOUSE), DEMOLITION_EXCEPTIONS, M)):
    f = a.audits_private / sample
    assert sha(f) == S["private_outputs_sha256"][sample]
    d = pd.read_csv(f, dtype=str, keep_default_na=False)
    assert set(exceptions) <= set(d.audit_id)
    d["class"] = [exceptions.get(i, default)[0] for i in d.audit_id]
    d["reason"] = [exceptions.get(i, default)[1] for i in d.audit_id]
    cols = ["audit_id", "permit_number", "permit_class", "class", "reason"] if name == "demolition_audit" else ["audit_id", "permit_number", "class", "reason"]
    d[cols].to_csv(a.out_dir / f"{name}_classes.csv", index=False)
    res = dict(sample_sha256=sha(f), n=len(d), classes=d["class"].value_counts().to_dict(),
               share=cp(int(d["class"].eq(positive).sum()), len(d)),
               reader="Claude (AI model), from the permit description only, one reading on 2026-11-10; not checked by an engineer or a second reader")
    if name == "label_audit":
        res["reasons_among_repairs"] = d.loc[d["class"].eq(R), "reason"].value_counts().to_dict()
    else:
        res["classes_by_permit_class"] = {k: v.to_dict() for k, v in d.groupby("permit_class")["class"].value_counts().unstack(fill_value=0).iterrows()}
    out[name] = res
(a.out_dir / "audit_results_2018.json").write_text(json.dumps(out, indent=1, default=int) + "\n")
print(json.dumps(out, indent=1, default=int))
