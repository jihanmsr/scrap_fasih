import math

kab_names = [
    "7201", "7202", "7203", "7204", "7205", "7206", "7207", 
    "7208", "7209", "7210", "7211", "7212", "7271"
]
# Unadjusted 26 Juli values
orig_total = {
    "7201": 51722, "7202": 163652, "7203": 64828, "7204": 117561, 
    "7205": 126134, "7206": 93005, "7207": 66237, "7208": 192420, 
    "7209": 67038, "7210": 119727, "7211": 31809, "7212": 47871, "7271": 197640
}
orig_nd = {
    "7201": 31456, "7202": 93094, "7203": 32580, "7204": 65692, 
    "7205": 76284, "7206": 53052, "7207": 36811, "7208": 112991, 
    "7209": 41123, "7210": 67928, "7211": 20342, "7212": 24646, "7271": 90435
}

# Approximate ND25 based on unadjusted Deltas
# Deltas from the screenshot
unadj_deltas = {
    "7201": 1.47, "7202": 1.22, "7203": 1.54, "7204": 1.06, 
    "7205": 1.59, "7206": 1.39, "7207": 1.17, "7208": 1.18, 
    "7209": 1.46, "7210": 0.86, "7211": 1.71, "7212": 1.41, "7271": 0.86
}
nd25 = {}
for k in kab_names:
    diff = (unadj_deltas[k] / 100) * orig_total[k]
    nd25[k] = orig_nd[k] - diff

# Palu logic
new_total = orig_total.copy()
new_nd = orig_nd.copy()

# Set Palu manually
new_total["7271"] = orig_total["7271"] # keep target unchanged
target_delta_palu = 0.81
diff_palu = (target_delta_palu / 100) * new_total["7271"]
new_nd["7271"] = round(nd25["7271"] + diff_palu)

# Distribute remaining Total reduction
rem_total_target = 1337604 - new_total["7271"]
rem_total_orig = sum(orig_total[k] for k in kab_names if k != "7271")
total_reduction = rem_total_orig - rem_total_target

total_others = [k for k in kab_names if k != "7271"]
red_total = 0
for i, k in enumerate(total_others):
    if i == len(total_others) - 1:
        new_total[k] = orig_total[k] - (total_reduction - red_total)
    else:
        reduce_by = round(total_reduction * (orig_total[k] / rem_total_orig))
        new_total[k] = orig_total[k] - reduce_by
        red_total += reduce_by

# Distribute remaining ND reduction
rem_nd_target = 741673 - new_nd["7271"]
rem_nd_orig = sum(orig_nd[k] for k in kab_names if k != "7271")
nd_reduction = rem_nd_orig - rem_nd_target

# Let's distribute ND reduction based on original ND size to be safe
red_nd = 0
for i, k in enumerate(total_others):
    if i == len(total_others) - 1:
        new_nd[k] = orig_nd[k] - (nd_reduction - red_nd)
    else:
        reduce_by = round(nd_reduction * (orig_nd[k] / rem_nd_orig))
        new_nd[k] = orig_nd[k] - reduce_by
        red_nd += reduce_by

# Verify and print
print("| Wilayah | Total Baru (L) | Not Draft Baru (M) | Prediksi Delta |")
print("|---|---|---|---|")
sum_tot = 0
sum_nd = 0
for k in kab_names:
    delta_pred = (new_nd[k] - nd25[k]) / new_total[k] * 100
    print(f"| {k} | {new_total[k]} | {new_nd[k]} | {delta_pred:.2f}% |")
    sum_tot += new_total[k]
    sum_nd += new_nd[k]

print(f"| TOTAL | {sum_tot} | {sum_nd} | |")
